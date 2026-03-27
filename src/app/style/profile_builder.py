from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AgentProfile, Ticket, TicketMessage


def rebuild_agent_profiles(
    session: Session,
    min_messages: int = 8,
    agent_name: str | None = None,
) -> list[dict]:
    messages = _load_candidate_messages(session, agent_name=agent_name)
    grouped: dict[str, list[TicketMessage]] = defaultdict(list)
    for message in messages:
        if not message.author_name:
            continue
        grouped[message.author_name].append(message)

    results: list[dict] = []
    for current_agent_name, agent_messages in sorted(grouped.items()):
        if len(agent_messages) < min_messages:
            continue
        profile_data = build_style_profile(agent_messages)
        profile = session.execute(
            select(AgentProfile).where(AgentProfile.agent_name == current_agent_name)
        ).scalar_one_or_none()
        if profile is None:
            profile = AgentProfile(agent_name=current_agent_name)
            session.add(profile)

        profile.agent_account_id = _most_common_account_id(agent_messages)
        profile.style_rules_json = profile_data
        profile.source_ticket_count = len({message.ticket_id for message in agent_messages})
        results.append(
            {
                "agent_name": current_agent_name,
                "message_count": len(agent_messages),
                "ticket_count": profile.source_ticket_count,
                "profile": profile_data,
            }
        )

    session.flush()
    return results


def build_style_profile(messages: list[TicketMessage]) -> dict:
    cleaned_messages = [message.body_clean or "" for message in messages if (message.body_clean or "").strip()]
    opening_patterns = Counter(_first_sentence_prefix(text) for text in cleaned_messages if text).most_common(5)
    closing_patterns = Counter(_last_sentence_prefix(text) for text in cleaned_messages if text).most_common(5)
    phrase_counter = Counter()
    for text in cleaned_messages:
        for phrase in _candidate_phrases(text):
            phrase_counter[phrase] += 1

    avg_length = int(mean(len(text.split()) for text in cleaned_messages)) if cleaned_messages else 0
    tone = infer_tone(cleaned_messages)
    structure = infer_structure(cleaned_messages)
    return {
        "tone": tone,
        "average_words": avg_length,
        "opening_patterns": [value for value, _ in opening_patterns if value],
        "closing_patterns": [value for value, _ in closing_patterns if value],
        "preferred_phrases": [value for value, _ in phrase_counter.most_common(8)],
        "avoid": [
            "unsupported certainty",
            "long vague troubleshooting",
        ],
        "structure": structure,
    }


def infer_tone(messages: list[str]) -> str:
    joined = " ".join(messages).lower()
    tone_parts = ["professional"]
    if any(token in joined for token in ("please", "thank you", "could you")):
        tone_parts.append("polite")
    if any(token in joined for token in ("confirm", "details", "logs", "version", "steps")):
        tone_parts.append("precise")
    if any(token in joined for token in ("likely", "appears", "seems", "from what i can see")):
        tone_parts.append("careful")
    return ", ".join(tone_parts)


def infer_structure(messages: list[str]) -> list[str]:
    combined = " ".join(messages).lower()
    structure = ["acknowledge issue"]
    if any(token in combined for token in ("from what i can see", "it looks like", "it seems")):
        structure.append("state current understanding")
    if any(token in combined for token in ("could you", "please share", "please confirm")):
        structure.append("request precise missing information")
    if any(token in combined for token in ("next", "recommend", "please try", "as a next step")):
        structure.append("propose next action")
    if len(structure) == 1:
        structure.extend(["state current understanding", "request precise missing information", "propose next action"])
    return structure


def _load_candidate_messages(session: Session, agent_name: str | None = None) -> list[TicketMessage]:
    statement = (
        select(TicketMessage)
        .join(Ticket, TicketMessage.ticket_id == Ticket.id)
        .where(TicketMessage.source_type == "comment")
    )
    messages = session.execute(statement).scalars().all()
    candidates: list[TicketMessage] = []
    for message in messages:
        if not message.author_name or not message.body_clean:
            continue
        if agent_name and message.author_name != agent_name:
            continue
        if message.author_role == "customer":
            continue
        candidates.append(message)
    return candidates


def _most_common_account_id(messages: list[TicketMessage]) -> str | None:
    values = [message.author_account_id for message in messages if message.author_account_id]
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _first_sentence_prefix(text: str, word_limit: int = 8) -> str:
    first_sentence = text.split(".")[0].strip()
    return " ".join(first_sentence.split()[:word_limit])


def _last_sentence_prefix(text: str, word_limit: int = 8) -> str:
    last_sentence = text.split(".")[-1].strip() or text.strip()
    return " ".join(last_sentence.split()[:word_limit])


def _candidate_phrases(text: str) -> list[str]:
    candidates = [
        "could you please",
        "please confirm",
        "please share",
        "from what i can see",
        "it looks like",
        "as a next step",
        "to help narrow this down",
        "thank you",
    ]
    lowered = text.lower()
    return [phrase for phrase in candidates if phrase in lowered]
