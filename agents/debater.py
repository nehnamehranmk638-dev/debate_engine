import os
from dotenv import load_dotenv
from openai import OpenAI
from retrieval.vector_store import build_dynamic_store

load_dotenv()

class DebaterAgent:
    def __init__(self, stance: str, topic: str):
        """
        stance: "PRO" or "AGAINST"
        topic: the debate topic
        """
        self.stance = stance
        self.topic = topic
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")

        # build the FAISS store for this agent's stance
        print(f"Initializing {stance} debater...")
        self.store = build_dynamic_store(topic, stance)
        print(f"{stance} debater ready.")

    def _retrieve_evidence(self, query: str, k: int = 3) -> list:
        """retrieve top k relevant chunks from this agent's store"""
        docs = self.store.similarity_search(query, k=k)
        return docs

    def _build_prompt(
        self,
        topic: str,
        evidence: list,
        opponent_arg: str,
        round_num: int
    ) -> tuple[str, str]:
        """build system and human messages for the LLM"""

        # format evidence chunks with their sources
        evidence_text = ""
        for i, doc in enumerate(evidence):
            title = doc.metadata.get("title", "Unknown source")
            evidence_text += f"\n[Evidence {i+1}] Source: {title}\n"
            evidence_text += doc.page_content + "\n"

        system_message = f"""You are a skilled, confident debate champion \
arguing the {self.stance} side of this topic.

Your rules:
1. Every claim you make MUST be supported by the provided evidence
2. Explicitly reference evidence by saying things like \
"According to [source]..." or "Evidence shows..."
3. Be specific — use facts, numbers, and examples from the evidence
4. Do NOT make up statistics or facts not in the evidence
5. Keep your argument to 4-5 sentences, sharp and focused
6. If this is not round 1, directly respond to your opponent's argument"""

        if opponent_arg:
            opponent_section = f"""
Your opponent just argued:
\"{opponent_arg}\"

Counter their argument directly while making your own case."""
        else:
            opponent_section = "This is the opening round. Make your strongest opening argument."

        human_message = f"""Debate topic: {topic}
Round: {round_num}
Your stance: {self.stance}

Evidence from your research:
{evidence_text}
{opponent_section}

Make your argument now:"""

        return system_message, human_message

    def argue(
        self,
        round_num: int,
        opponent_arg: str = ""
    ) -> dict:
        """
        generate an argument for the given round
        returns dict with argument, sources, evidence used
        """
        # retrieve relevant evidence
        search_query = self.topic
        if opponent_arg:
            # if opponent argued something, retrieve evidence
            # relevant to countering it
            search_query = f"{self.topic} {opponent_arg[:100]}"

        docs = self._retrieve_evidence(search_query, k=3)

        # build prompt
        system_msg, human_msg = self._build_prompt(
            topic=self.topic,
            evidence=docs,
            opponent_arg=opponent_arg,
            round_num=round_num
        )

        # call LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": human_msg}
            ],
            temperature=0.7,
            max_tokens=400
        )

        argument = response.choices[0].message.content.strip()

        # extract sources used
        sources = list(set([
            doc.metadata.get("title", "Unknown")
            for doc in docs
        ]))

        # store evidence text for judge to verify later
        evidence_used = "\n---\n".join([
            f"[{doc.metadata.get('title','?')}]: {doc.page_content}"
            for doc in docs
        ])

        return {
            "stance": self.stance,
            "round": round_num,
            "argument": argument,
            "sources": sources,
            "evidence_used": evidence_used
        }