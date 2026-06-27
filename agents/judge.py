import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class JudgeAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")

    def _extract_json(self, text: str) -> dict:
        """
        safely extract JSON from LLM response.
        LLMs sometimes wrap JSON in markdown code blocks
        or add extra text — this handles all cases.
        """
        # try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # try extracting from markdown code block
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # try finding raw JSON object in text
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # if all fails return default scores
        print("WARNING: Judge could not parse JSON. Using default scores.")
        return self._default_score("Could not parse judge response")

    def _default_score(self, reason: str) -> dict:
        """fallback score if JSON parsing fails"""
        return {
            "factual_grounding": 5,
            "logical_coherence": 5,
            "responsiveness": 5,
            "hallucination_penalty": 0,
            "total": 15,
            "reasoning": reason
        }

    def _clamp(self, value, min_val, max_val):
        """ensure scores stay within valid range"""
        return max(min_val, min(max_val, value))

    def evaluate(
        self,
        topic: str,
        stance: str,
        argument: str,
        evidence_used: str,
        opponent_arg: str = "",
        round_num: int = 1
    ) -> dict:
        """
        evaluate a single argument and return scores.
        this is the core judge function.
        """

        system_message = """You are a strict, impartial debate judge with \
expertise in logical reasoning and fact-checking.

Your job is to evaluate debate arguments based on:
1. Whether claims are actually supported by the provided evidence
2. Whether the argument is logically coherent
3. Whether the argument responds to the opponent

You must be STRICT about hallucination — if the debater makes a specific \
claim that is NOT in the evidence, penalize heavily.

You MUST respond with ONLY a valid JSON object. No other text. \
No markdown. No explanation outside the JSON."""

        opponent_section = ""
        if opponent_arg and round_num > 1:
            opponent_section = f"""
Opponent's argument this debater should respond to:
\"{opponent_arg}\"
"""

        human_message = f"""Evaluate this debate argument strictly.

Topic: {topic}
Stance being argued: {stance}
Round: {round_num}
{opponent_section}
Argument made by debater:
\"{argument}\"

Evidence the debater had access to (and ONLY this):
{evidence_used}

Score this argument and return ONLY this JSON object:
{{
    "factual_grounding": <integer 1-10, how well claims are supported by evidence>,
    "logical_coherence": <integer 1-10, how logical and structured the argument is>,
    "responsiveness": <integer 1-10, how well it addresses the opponent or topic>,
    "hallucination_penalty": <integer 0-5, penalty for claims not in evidence>,
    "reasoning": "<2-3 sentences explaining your scores>",
    "total": <factual_grounding + logical_coherence + responsiveness - hallucination_penalty>
}}

Be strict. A claim not found in the evidence = hallucination penalty."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": human_message}
            ],
            temperature=0.0,
            max_tokens=400
        )

        raw = response.choices[0].message.content.strip()
        scores = self._extract_json(raw)

        # clamp all scores to valid ranges
        scores["factual_grounding"] = self._clamp(
            scores.get("factual_grounding", 5), 1, 10
        )
        scores["logical_coherence"] = self._clamp(
            scores.get("logical_coherence", 5), 1, 10
        )
        scores["responsiveness"] = self._clamp(
            scores.get("responsiveness", 5), 1, 10
        )
        scores["hallucination_penalty"] = self._clamp(
            scores.get("hallucination_penalty", 0), 0, 5
        )

        # always recalculate total to prevent LLM math errors
        scores["total"] = (
            scores["factual_grounding"] +
            scores["logical_coherence"] +
            scores["responsiveness"] -
            scores["hallucination_penalty"]
        )

        return scores

    def verdict(
        self,
        topic: str,
        pro_results: list,
        against_results: list
    ) -> dict:
        """
        calculate final verdict after all rounds.
        takes list of round results for each side.
        """
        pro_scores = [r["pro_score"] for r in pro_results]
        against_scores = [r["against_score"] for r in pro_results]

        pro_total = sum(s["total"] for s in pro_scores)
        against_total = sum(s["total"] for s in against_scores)
        margin = abs(pro_total - against_total)

        if pro_total > against_total:
            winner = "PRO"
            winner_reason = "PRO side presented better grounded arguments"
        elif against_total > pro_total:
            winner = "AGAINST"
            winner_reason = "AGAINST side presented better grounded arguments"
        else:
            winner = "DRAW"
            winner_reason = "Both sides scored equally"

        return {
            "winner": winner,
            "winner_reason": winner_reason,
            "pro_total": pro_total,
            "against_total": against_total,
            "margin": margin,
            "rounds_played": len(pro_results)
        }