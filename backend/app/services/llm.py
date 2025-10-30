from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, cast
from zoneinfo import ZoneInfo

import dateparser
from pydantic import BaseModel, Field
from rapidfuzz import fuzz

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from app.core.config import get_settings
from app.schemas.quiz import QuizItem
from app.schemas.study import SummaryNote, SummaryQnASeed, SummarySection
from app.schemas.todo import TodoDraft
from app.services.cache import cache
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


class TodoBatch(BaseModel):
    items: List[TodoDraft] = Field(min_length=1, max_length=10)


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
        llm = ChatOpenAI(model=model, temperature=0.2, timeout=20, max_retries=1)
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

    @cache(ttl=86400)
    async def _summarize_cached(
        self, text: str, context: str, truncated: bool, user_request: str
    ) -> SummaryNote:
        parser = PydanticOutputParser(pydantic_object=SummaryNote)
        format_instructions = parser.get_format_instructions()
        system_prompt = """You are an academic study assistant that answers user requests about the supplied material.
Your job is to help with ANY study-relevant request such as:
- extracting key URLs (e.g., course page, handbook entry, assessment links),
- summarising course content and learning outcomes,
- generating clear, structured notes,
- answering factual questions about prerequisites, delivery mode, key dates, and assessments,
- surfacing actionable advice for students based only on the supplied content.

STRICTLY follow these principles:
1) Grounding: Use ONLY the supplied material (PRIMARY MATERIAL + ADDITIONAL CONTEXT). If something is missing or unclear, state "not found in provided material."
2) No code: Do NOT write source code, scripts, shell commands, or pseudo-code.
3) Honesty about limits: If input is truncated or context is missing, explicitly note it in the output.
4) Formatting: Output must be valid JSON that matches the provided schema exactly. Use the format instructions: {format_instructions}. If a field has no evidence, leave it empty as allowed by the schema.

Task selection:
- If the user_request is specific, perform that task precisely.
- If the user_request is "auto" or empty, provide: (a) a concise TL;DR, (b) structured notes with concrete facts (topics, outcomes, delivery, assessment, dates), and (c) helpful study Q&A seeds - all grounded in the material.

Content selection guidance:
- Ignore navigation chrome, cookie banners, ads, and boilerplate.
- Prefer academically relevant details: unit descriptions, outcomes, topics, delivery modes, prerequisites, assessments with weightings and deadlines, key dates, staff/contact, and study tips derived from the material.
- When URLs are present, extract the most canonical or official ones and place them in the most appropriate output fields.

Conciseness: Be concise but prioritise clarity and factual density over strict word limits.

Remember: produce JSON only, conforming to the schema given by the format instructions."""
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
                return LLMResult(summary, fallback_used=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM summarization failed: %s", exc)
        fallback = self._fallback_summary(truncated_text)
        if truncated:
            fallback.tldr = fallback.tldr[:150] + " (source truncated)"
        return LLMResult(fallback, fallback_used=True)

    @cache(ttl=86400)
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

    @cache(ttl=43200)
    async def _todo_cached(self, text: str) -> List[TodoDraft]:
        parser = PydanticOutputParser(pydantic_object=TodoBatch)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Extract actionable tasks. Titles must start with a verb, be concise, and suitable for a to-do list."
                    " Include due_at as ISO8601 when unambiguous or omit it. Avoid logging or echoing sensitive data.",
                ),
                ("human", "SOURCE:\n{text}"),
            ]
        )
        llm = self._llm
        if llm is None:
            raise RuntimeError("LLM not initialised")
        chain: RunnableSerializable[Any, Any] = prompt | llm | parser
        batch = await chain.ainvoke({"text": text})
        todo_batch = cast(TodoBatch, batch)
        return list(todo_batch.items)

    def _normalise_todos(self, drafts: List[TodoDraft]) -> List[TodoDraft]:
        normalised: List[TodoDraft] = []
        try:
            tz = ZoneInfo(self.settings.default_timezone)
        except Exception:  # pragma: no cover - fallback when tz unavailable
            tz = ZoneInfo("UTC")
        seen_titles: set[str] = set()
        for draft in drafts:
            title = draft.title.strip()
            if not title:
                continue
            lower_title = title.lower()
            if lower_title in seen_titles:
                continue
            seen_titles.add(lower_title)
            due_at = draft.due_at
            confidence = draft.due_at_confidence
            parsed_dt = None
            if isinstance(due_at, str):
                parsed_dt = dateparser.parse(
                    due_at,
                    settings={
                        "RETURN_AS_TIMEZONE_AWARE": True,
                        "PREFER_DATES_FROM": "future",
                        "TIMEZONE": self.settings.default_timezone,
                    },
                )
            elif due_at is not None:
                parsed_dt = due_at
            if parsed_dt is None:
                normalised.append(
                    TodoDraft(title=title, due_at=None, due_at_confidence=confidence or "low")
                )
            else:
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=tz)
                    confidence = confidence or "low"
                else:
                    confidence = confidence or "high"
                normalised.append(
                    TodoDraft(title=title, due_at=parsed_dt, due_at_confidence=confidence)
                )
        return normalised

    async def extract_todos(self, text: str) -> LLMResult:
        truncated_text, _ = self._truncate(text)
        if self.has_llm:
            try:
                drafts = await self._todo_cached(truncated_text)
                normalised = self._normalise_todos(drafts)
                if normalised:
                    return LLMResult(normalised, fallback_used=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM todo extraction failed: %s", exc)
        return LLMResult(self._fallback_todos(text), fallback_used=True)

    def _fallback_email_summary(self, body: str) -> str:
        first_line = body.strip().split(".")[0]
        keywords = ", ".join({word.strip(",") for word in body.split()[:5]})
        return f"{first_line.strip()}. Keywords: {keywords}"

    def _extract_fallback_key_points(self, subject: str, body: str) -> List[str]:
        """Extract simple key points from email when LLM is unavailable."""
        points = []
        
        # Try to extract sentences from body
        sentences = [s.strip() for s in body.split(".") if len(s.strip()) > 20]
        
        # Add subject as first point if meaningful
        if len(subject) > 10:
            points.append(f"Subject: {subject[:80]}")
        
        # Add first few sentences as points
        for sentence in sentences[:3]:
            if len(sentence) > 15:
                points.append(sentence[:100])
        
        return points[:4]  # Max 4 points

    def _categorize_email_fallback(self, subject: str, sender: str) -> str:
        """Categorize email based on keywords when LLM is unavailable."""
        combined = f"{subject} {sender}".lower()
        
        # Academic keywords
        if any(word in combined for word in ["assignment", "lecture", "course", "exam", "quiz", "tutorial", "lab", "submission"]):
            return "academic"
        
        # Administrative keywords
        if any(word in combined for word in ["enrollment", "enrol", "admin", "register", "fee", "payment", "official", "university"]):
            return "administrative"
        
        # Social keywords
        if any(word in combined for word in ["event", "party", "club", "social", "meet", "gathering", "rsvp"]):
            return "social"
        
        # Promotional keywords
        if any(word in combined for word in ["sale", "offer", "discount", "deal", "promo", "buy", "shop", "limited time"]):
            return "promotional"
        
        # Notification keywords
        if any(word in combined for word in ["notification", "alert", "reminder", "update", "confirm"]):
            return "notification"
        
        # Newsletter keywords
        if any(word in combined for word in ["newsletter", "digest", "bulletin", "weekly", "monthly"]):
            return "newsletter"
        
        return "other"

    def _fallback_summary(self, text: str) -> SummaryNote:
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
        qna = [
            SummaryQnASeed(q="What is the central argument?", a_hint=core_points[0][:120]),
            SummaryQnASeed(q="Which evidence backs the main idea?", a_hint=supporting[0][:120]),
            SummaryQnASeed(q="What should be done next?", a_hint=implications[0][:120]),
        ]
        return SummaryNote(tldr=tldr[:200], sections=sections, qna_seeds=qna)

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
        ]
        items: list[QuizItem] = []
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        for sentence in sentences[:3]:
            options = [sentence, f"Not {sentence}", "Related concept", "Background detail"]
            items.append(
                QuizItem(
                    stem=f"Which statement aligns with: {sentence[:70]}?",
                    options=options,
                    answer_index=0,
                    rationale="This option restates the main sentence, aligning with the source notes.",
                    generated_from="template",
                )
            )
        items.extend(template_pool)
        return items[:5]

    def _fallback_todos(self, text: str) -> list[TodoDraft]:
        drafts: list[TodoDraft] = []
        lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
        if not lines:
            drafts.append(TodoDraft(title="Review notes", due_at=None, due_at_confidence="low"))
            return drafts
        for line in lines:
            drafts.append(TodoDraft(title=line, due_at=None, due_at_confidence="low"))
        return drafts


__all__ = ["LLMService", "LLMResult", "EmailAnalysis"]
