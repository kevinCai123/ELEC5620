from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, cast

from pydantic import BaseModel, Field
from rapidfuzz import fuzz

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from app.core.config import get_settings
from app.schemas.quiz import QuizItem
from app.schemas.study import SummaryNote, SummarySection
from app.services.rag import get_retriever

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency for offline usage
    ChatOpenAI = None  # type: ignore

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 20_000
QUIZ_DUPLICATE_THRESHOLD = 90


class QuizBatch(BaseModel):
    items: List[QuizItem] = Field(min_length=5, max_length=5)


class EmailAnalysis(BaseModel):
    """Structured email analysis with summary, key points, and category."""
    summary: str = Field(description="1-2 sentence summary of the email")
    key_points: List[str] = Field(description="2-4 key action items or important points from the email", min_length=0, max_length=4)
    category: str = Field(description="Email category: academic, administrative, social, promotional, notification, newsletter, personal, or other")


@dataclass
class LLMResult:
    data: Any
    fallback_used: bool


class LLMService:
    """Wrapper around LangChain models with graceful fallbacks when unavailable."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._llm: Optional[RunnableSerializable[Any, Any]] = self._init_llm()
        self._retriever: Optional[Callable[[str], List[Document]]] = None
        try:
            self._retriever = get_retriever()
        except Exception as exc:  # pragma: no cover - RAG optional
            logger.info("RAG retriever unavailable: %s", exc)

    def _init_llm(self) -> Optional[RunnableSerializable[Any, Any]]:
        if ChatOpenAI is None:
            logger.warning("langchain-openai package missing; using fallback implementations")
            return None
        api_key = self.settings.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY missing; using fallback implementations")
            return None
        model = self.settings.openai_model
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        # Timeout extended to 20 minutes for demo environments with slow network speeds.
        # max_retries=3 for better reliability on unstable connections
        llm = ChatOpenAI(model=model, temperature=0.2, timeout=1200, max_retries=3)
        logger.info("ChatOpenAI initialised", extra={"model": model})
        return cast(RunnableSerializable[Any, Any], llm)

    @property
    def has_llm(self) -> bool:
        return self._llm is not None

    def _truncate(self, text: str) -> tuple[str, bool]:
        if len(text) <= MAX_INPUT_CHARS:
            return text, False
        truncated = text[:MAX_INPUT_CHARS] + " …[truncated]"
        return truncated, True

    def _build_context(self, query: str) -> str:
        if not self._retriever:
            return ""
        try:
            docs = self._retriever(query)
        except Exception as exc:  # pragma: no cover - retrieval failure
            logger.debug("RAG retrieval failed: %s", exc)
            return ""
        snippets: List[str] = []
        for idx, doc in enumerate(docs[:5], start=1):
            source = doc.metadata.get("source", f"chunk-{idx}")
            snippet = doc.page_content.replace("\n", " ")
            snippets.append(f"[{idx}] {source}: {snippet}")
        context = "\n".join(snippets)
        if len(context) > MAX_INPUT_CHARS:
            context = context[: MAX_INPUT_CHARS // 2] + " …[context truncated]"
        return context

    # =========================
    #       SUMMARIZATION
    # =========================

    # Cache disabled - always generate fresh summaries
    async def _summarize_cached(
        self, text: str, context: str, truncated: bool, user_request: str
    ) -> SummaryNote:
        """
        NOTE: Q&A seeds have been removed by design. We focus on TL;DR + structured sections only.
        """
        parser = PydanticOutputParser(pydantic_object=SummaryNote)
        format_instructions = parser.get_format_instructions()
        system_prompt = """You are an academic study assistant that answers user requests about the supplied material.

Your job is to help with study-relevant tasks such as:
- summarising course or document content,
- producing clean, structured notes with headings and concise bullets,
- answering factual questions about prerequisites, delivery mode, key dates, and assessments (based ONLY on supplied content),
- extracting important links that appear in the text.

STRICTLY follow these principles:
1) Grounding: Use ONLY the supplied material (PRIMARY MATERIAL + ADDITIONAL CONTEXT). If something is missing or unclear, state "not found in provided material."
2) No code: Do NOT write source code, shell commands, or pseudo-code.
3) Honesty about limits: If input is truncated or context is missing, explicitly note it in the output.
4) Formatting: Output must be valid JSON that matches the provided schema exactly. Use the format instructions: {format_instructions}. If a field has no evidence, leave it empty as allowed by the schema.

Task selection:
- If user_request is specific, perform ONLY that task.
- If user_request is "auto" or empty, produce: (a) a concise TL;DR and (b) well-structured sections surfacing concrete facts (topics, outcomes, delivery, assessments, dates, contacts).
"""
        human_prompt = """USER REQUEST:
{user_request}

PRIMARY MATERIAL:
{text}

ADDITIONAL CONTEXT:
{context}

Input state: {truncated_notice}"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", human_prompt),
            ]
        ).partial(format_instructions=format_instructions)
        llm = self._llm
        if llm is None:
            raise RuntimeError("LLM not initialised")
        chain: RunnableSerializable[Any, Any] = prompt | llm | parser
        truncated_notice = "Input truncated" if truncated else "Complete input"
        result = await chain.ainvoke(
            {
                "text": text,
                "context": context or "(no context)",
                "truncated_notice": truncated_notice,
                "user_request": user_request,
            }
        )
        return cast(SummaryNote, result)

    def _enforce_summary_limits(self, note: SummaryNote, truncated: bool) -> SummaryNote:
        words = note.tldr.split()
        if len(words) > 50:
            note.tldr = " ".join(words[:50]) + " …"
        if truncated:
            note.tldr = note.tldr.rstrip(".") + " (source truncated)"
        return note

    async def summarize(self, text: str, user_request: str = "auto") -> LLMResult:
        truncated_text, truncated = self._truncate(text)
        context = self._build_context(truncated_text)
        if self.has_llm:
            try:
                summary = await self._summarize_cached(
                    truncated_text, context, truncated, user_request=user_request
                )
                summary = self._enforce_summary_limits(summary, truncated)
                # Ensure qna_seeds is empty to remove Q&A from outputs, even if schema contains the field.
                if hasattr(summary, "qna_seeds"):
                    try:
                        summary.qna_seeds = []
                    except Exception:
                        pass
                return LLMResult(summary, fallback_used=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM summarization failed: %s", exc)
        fallback = self._fallback_summary(truncated_text)
        if truncated:
            fallback.tldr = fallback.tldr[:150] + " (source truncated)"
        return LLMResult(fallback, fallback_used=True)

    # =========================
    #       QUIZ (original behavior)
    # =========================

    # Cache disabled - always generate fresh quizzes
    async def _quiz_cached(self, text: str, context: str, truncated: bool) -> List[QuizItem]:
        parser = PydanticOutputParser(pydantic_object=QuizBatch)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Generate exactly five multiple-choice questions covering distinct key points."
                    " Each item must include stem, four options, answer_index, and rationale."
                    " Avoid duplicates and ensure options are concise. Output JSON only.",
                ),
                (
                    "human",
                    "PRIMARY MATERIAL:\n{text}\n\nSUPPLEMENTAL CONTEXT:\n{context}\n\nInput state: {truncated_notice}",
                ),
            ]
        )
        llm = self._llm
        if llm is None:
            raise RuntimeError("LLM not initialised")
        chain: RunnableSerializable[Any, Any] = prompt | llm | parser
        truncated_notice = "Input truncated" if truncated else "Complete input"
        batch = await chain.ainvoke(
            {"text": text, "context": context or "(no context)", "truncated_notice": truncated_notice}
        )
        quiz_batch = cast(QuizBatch, batch)
        return list(quiz_batch.items)

    def _deduplicate_quiz_items(self, items: List[QuizItem]) -> List[QuizItem]:
        unique: List[QuizItem] = []
        stems: List[str] = []
        for item in items:
            if any(fuzz.ratio(item.stem, stem) >= QUIZ_DUPLICATE_THRESHOLD for stem in stems):
                continue
            unique.append(item)
            stems.append(item.stem)
        return unique

    def _top_up_quiz_items(self, items: List[QuizItem], source_text: str) -> List[QuizItem]:
        fallback_items = self._fallback_quiz(source_text)
        for fallback_item in fallback_items:
            if len(items) >= 5:
                break
            if any(fuzz.ratio(fallback_item.stem, item.stem) >= QUIZ_DUPLICATE_THRESHOLD for item in items):
                continue
            items.append(fallback_item)
        return items

    async def generate_quiz(self, text: str) -> LLMResult:
        truncated_text, truncated = self._truncate(text)
        context = self._build_context(truncated_text)
        if self.has_llm:
            try:
                items = await self._quiz_cached(truncated_text, context, truncated)
                items = self._deduplicate_quiz_items(items)
                if len(items) < 5:
                    items = self._top_up_quiz_items(items, text)
                return LLMResult(items[:5], fallback_used=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM quiz generation failed: %s", exc)
        return LLMResult(self._fallback_quiz(text), fallback_used=True)

    # =========================
    #       EMAIL ANALYSIS
    # =========================

    async def summarize_email(self, subject: str, sender: str, body: str) -> LLMResult:
        trimmed_body, _ = self._truncate(body)
        if self.has_llm:
            parser = PydanticOutputParser(pydantic_object=EmailAnalysis)
            format_instructions = parser.get_format_instructions()

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You analyze emails and extract key information in a structured format.\n"
                        "Your task:\n"
                        "1. Write a concise 1-2 sentence summary focusing on the main purpose and any required actions\n"
                        "2. Extract 2-4 key action items or important points (be specific and actionable)\n"
                        "3. Categorize the email into one of these types:\n"
                        "   - academic: Course-related, assignments, lectures, study materials\n"
                        "   - administrative: University admin, enrollment, fees, official notices\n"
                        "   - social: Events, clubs, social gatherings, student activities\n"
                        "   - promotional: Marketing, offers, advertisements, promotions\n"
                        "   - notification: System notifications, updates, reminders\n"
                        "   - newsletter: Regular updates, bulletins, news digests\n"
                        "   - personal: Personal communication from individuals\n"
                        "   - other: Anything that doesn't fit above categories\n\n"
                        "Output JSON only. Format: {format_instructions}",
                    ),
                    (
                        "human",
                        "Subject: {subject}\nFrom: {sender}\n\nBody:\n{body}",
                    ),
                ]
            ).partial(format_instructions=format_instructions)

            try:
                llm = self._llm
                if llm is None:
                    raise RuntimeError("LLM not initialised")
                chain: RunnableSerializable[Any, Any] = prompt | llm | parser
                analysis = await chain.ainvoke({"subject": subject, "sender": sender, "body": trimmed_body})
                return LLMResult(cast(EmailAnalysis, analysis), fallback_used=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM email analysis failed: %s", exc)

        # Fallback
        fallback_summary = self._fallback_email_summary(trimmed_body)
        fallback_analysis = EmailAnalysis(
            summary=fallback_summary,
            key_points=self._extract_fallback_key_points(subject, trimmed_body),
            category=self._categorize_email_fallback(subject, sender),
        )
        return LLMResult(fallback_analysis, fallback_used=True)

    async def generate_email_digest_simple(self, combined_email_text: str) -> LLMResult:
        """Generate a comprehensive digest summary from multiple email summaries with tasks & deadlines."""
        if self._llm is not None:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            from pydantic import BaseModel, Field

            class DigestSummary(BaseModel):
                overview: str = Field(description="2-3 sentence overview of the main themes across emails")
                highlights: list[str] = Field(
                    default_factory=list,
                    description="4-6 key highlights capturing the most important information",
                )
                action_items: list[str] = Field(
                    default_factory=list,
                    description="3-5 actionable next steps that require attention",
                )
                tasks_and_deadlines: list[str] = Field(
                    default_factory=list,
                    description="3-7 tasks with due dates when available (format: 'Task description (Due: YYYY-MM-DD)')",
                )

            parser = JsonOutputParser(pydantic_object=DigestSummary)

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are analyzing a batch of email summaries to create a comprehensive digest.\n"
                        "Your task:\n"
                        "1. Write a brief overview paragraph (2-3 sentences) summarizing the main themes.\n"
                        "2. Extract 4-6 key highlights across all emails (most important information).\n"
                        "3. List 3-5 action items that require attention.\n"
                        "4. List 3-7 tasks with deadlines (format: 'Task description (Due: YYYY-MM-DD)' or just 'Task description' if no date).\n\n"
                        "{format_instructions}\n\n"
                        "Return only valid JSON matching the schema."
                    ),
                    (
                        "human",
                        "Email Summaries:\n\n{email_summaries}"
                    ),
                ]
            ).partial(format_instructions=parser.get_format_instructions())

            try:
                llm = self._llm
                chain = prompt | llm | parser
                digest_summary = await chain.ainvoke({"email_summaries": combined_email_text})

                if isinstance(digest_summary, DigestSummary):
                    digest_data = digest_summary.model_dump()
                elif isinstance(digest_summary, dict):
                    digest_data = digest_summary
                else:
                    digest_data = DigestSummary.model_validate(digest_summary).model_dump()

                return LLMResult(digest_data, fallback_used=False)

            except Exception as exc:
                logger.warning("LLM email digest generation failed: %s", exc)
        
        # Fallback
        fallback_digest = {
            "overview": "Summary of recent emails (LLM unavailable)",
            "highlights": ["Email digest requires AI to be enabled"],
            "action_items": ["Configure OpenAI API key to generate intelligent digests"],
            "tasks_and_deadlines": ["Review emails for important deadlines"]
        }
        return LLMResult(fallback_digest, fallback_used=True)


    # =========================
    #        FALLBACKS
    # =========================

    def _fallback_email_summary(self, body: str) -> str:
        first_line = body.strip().split(".")[0]
        keywords = ", ".join({word.strip(",") for word in body.split()[:5]})
        return f"{first_line.strip()}. Keywords: {keywords}"

    def _extract_fallback_key_points(self, subject: str, body: str) -> List[str]:
        """Extract simple key points from email when LLM is unavailable."""
        points = []
        sentences = [s.strip() for s in body.split(".") if len(s.strip()) > 20]
        if len(subject) > 10:
            points.append(f"Subject: {subject[:80]}")
        for sentence in sentences[:3]:
            if len(sentence) > 15:
                points.append(sentence[:100])
        return points[:4]  # Max 4 points

    def _categorize_email_fallback(self, subject: str, sender: str) -> str:
        """Categorize email based on keywords when LLM is unavailable."""
        combined = f"{subject} {sender}".lower()
        if any(word in combined for word in ["assignment", "lecture", "course", "exam", "quiz", "tutorial", "lab", "submission"]):
            return "academic"
        if any(word in combined for word in ["enrollment", "enrol", "admin", "register", "fee", "payment", "official", "university"]):
            return "administrative"
        if any(word in combined for word in ["event", "party", "club", "social", "meet", "gathering", "rsvp"]):
            return "social"
        if any(word in combined for word in ["sale", "offer", "discount", "deal", "promo", "buy", "shop", "limited time"]):
            return "promotional"
        if any(word in combined for word in ["notification", "alert", "reminder", "update", "confirm"]):
            return "notification"
        if any(word in combined for word in ["newsletter", "digest", "bulletin", "weekly", "monthly"]):
            return "newsletter"
        return "other"

    def _fallback_summary(self, text: str) -> SummaryNote:
        """
        Fallback summary with NO Q&A seeds.
        """
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        tldr = " ".join(sentences[:2]) if len(sentences) >= 2 else (sentences[0] if sentences else text[:160])
        core_points = sentences[:3] or [tldr]
        supporting = sentences[3:6] or ["Source material too short for additional supporting detail."]
        implications = sentences[6:9] or ["Review the material directly to extract next actions."]
        sections = [
            SummarySection(heading="Core Ideas", bullets=core_points[:3]),
            SummarySection(heading="Supporting Details", bullets=supporting[:3]),
            SummarySection(heading="Implications & Next Steps", bullets=implications[:3]),
        ]
        # Ensure qna_seeds is empty/absent depending on schema. If SummaryNote requires the field, set to [].
        return SummaryNote(tldr=tldr[:200], sections=sections, qna_seeds=[])

    def _fallback_quiz(self, text: str) -> list[QuizItem]:
        template_pool = [
            QuizItem(
                stem="What is the primary objective discussed in the notes?",
                options=[
                    "To review background theory",
                    "To outline the main methodology",
                    "To list references",
                    "To describe unrelated topics",
                ],
                answer_index=1,
                rationale="The notes focus on the key methodology, so option 2 is correct.",
                generated_from="template",
            ),
            QuizItem(
                stem="Which challenge is highlighted in the material?",
                options=[
                    "Resource constraints",
                    "Lack of interest",
                    "Overabundance of data",
                    "Perfect execution",
                ],
                answer_index=0,
                rationale="The notes mention managing limited resources as a core issue.",
                generated_from="template",
            ),
            QuizItem(
                stem="What is the central concept covered in this material?",
                options=[
                    "An overview of the main ideas",
                    "A list of unrelated facts",
                    "A biography of contributors",
                    "A set of random definitions",
                ],
                answer_index=0,
                rationale="The material emphasizes the main concepts, making option A the best choice.",
                generated_from="template",
            ),
            QuizItem(
                stem="Which aspect is most emphasized in the content?",
                options=[
                    "Practical applications",
                    "Historical background only",
                    "Future predictions",
                    "Irrelevant tangents",
                ],
                answer_index=0,
                rationale="The content focuses on practical applications and real-world use cases.",
                generated_from="template",
            ),
            QuizItem(
                stem="What conclusion can be drawn from the material?",
                options=[
                    "The topic requires further study and practice",
                    "Everything is fully understood",
                    "No action is needed",
                    "The subject is completely irrelevant",
                ],
                answer_index=0,
                rationale="The material suggests continued learning and application of concepts.",
                generated_from="template",
            ),
        ]
        # Return 5 varied template questions instead of sentence-based ones
        return template_pool[:5]


__all__ = ["LLMService", "LLMResult", "EmailAnalysis"]
