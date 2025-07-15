import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from judgeval import JudgmentClient
from judgeval.tracer import Tracer, wrap
from judgeval.data import Example
from judgeval.scorers import (
    AnswerRelevancyScorer,
    AnswerCorrectnessScorer,
    FaithfulnessScorer,
    InstructionAdherenceScorer
)
from judgeval.scorers.example_scorer import ExampleScorer
import time

# --- 1. Initialize Flask App ---
app = Flask(__name__)
CORS(app)

# --- 2. Configuration & Setup ---
# IMPORTANT: Set these environment variables in your terminal before running.
# export OPENAI_API_KEY="sk-..."
# export JUDGMENT_API_KEY="..."
# export JUDGMENT_ORG_ID="..."

try:
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    JUDGMENT_API_KEY = os.environ["JUDGMENT_API_KEY"]
    JUDGMENT_ORG_ID = os.environ["JUDGMENT_ORG_ID"]

    traced_client = wrap(OpenAI(api_key=OPENAI_API_KEY))
    untraced_client = OpenAI(api_key=OPENAI_API_KEY)
    judgment_client = JudgmentClient(api_key=JUDGMENT_API_KEY, organization_id=JUDGMENT_ORG_ID)
    judgment_tracer = Tracer(project_name="interactive-agent-grader-app", api_key=JUDGMENT_API_KEY, organization_id=JUDGMENT_ORG_ID)

except KeyError as e:
    print(f"🚨 Missing environment variable: {e}. Please set it before running.")
    exit()

print("✅ Successfully initialized OpenAI and Judgment clients.")
print("🚀 Python backend server is ready.")

# --- 3. Custom Empathy Scorer ---
class EmpathyScorer(ExampleScorer):
    name: str = "Empathy Score"

    async def a_score_example(self, example: Example) -> float:
        eval_prompt = f"Analyze the agent's response for empathy... The agent's response was: \"{example.actual_output}\"\n\nReturn only a single floating point number between 0.0 and 1.0..."
        try:
            response = untraced_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": eval_prompt}])
            score = float(response.choices[0].message.content.strip())
            self.reason = f"LLM judge rated empathy as {score:.2f}."
            return score
        except Exception as e:
            self.reason = f"Scoring failed: {e}"
            return 0.0

# --- 4. Agent Definitions ---
@judgment_tracer.observe(span_type="function")
def run_agent(agent_type: str, customer_query: str, retrieval_context: list, expected_output: str, scorers: list):
    if agent_type == 'A':
        system_prompt = "You are a customer support agent. Your responses must be professional, concise, and to the point... Instruction: Directly answer the user's question."
    else:
        system_prompt = "You are a customer support agent. Your primary goal is to make the customer feel heard and valued... Instruction: Start your response by acknowledging the user's situation..."
    
    context_str = "\n".join(retrieval_context)
    final_prompt = f"Retrieval Context: \"{context_str}\"\n\nCustomer Query: \"{customer_query}\""
    response = traced_client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": final_prompt}])
    response_content = response.choices[0].message.content
    
    judgment_tracer.async_evaluate(
        scorers=scorers,
        example=Example(input=customer_query, actual_output=response_content, expected_output=expected_output, retrieval_context=retrieval_context),
        model="gpt-4o"
    )
    return response_content

# --- 5. API Endpoint ---
@app.route('/run_test', methods=['POST'])
def run_test_endpoint():
    data = request.json
    user_query = data.get('query')
    if not user_query:
        return jsonify({"error": "Query not provided"}), 400

    # a. E-commerce Guardrail
    guardrail_prompt = f'Is the following user query related to e-commerce (e.g., orders, shipping, returns, products, payments)? Respond with only "Yes" or "No".\n\nQuery: "{user_query}"'
    guardrail_res = untraced_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": guardrail_prompt}])
    is_ecommerce_query = guardrail_res.choices[0].message.content.strip()

    if "no" in is_ecommerce_query.lower():
        return jsonify({"error": "Query is not relevant to e-commerce. Please ask a question about orders, shipping, returns, etc."}), 422 # Unprocessable Entity

    # b. Dynamically generate the test case
    context_gen_prompt = f'You are a policy author for an e-commerce company. A customer has the following query: "{user_query}". Write a short, factual company policy that would be the source of truth for answering this query. Output ONLY the policy text itself, without any introduction or conversational text.'
    context_res = untraced_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": context_gen_prompt}])
    context = context_res.choices[0].message.content

    expected_gen_prompt = f'You are a helpful assistant. Based on the customer query and the relevant company policy, generate the ideal "golden" answer. Output ONLY the answer text itself.\n\nCustomer Query: "{user_query}"\n\nCompany Policy: "{context}"\n\nGolden Answer:'
    expected_res = untraced_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": expected_gen_prompt}])
    expected = expected_res.choices[0].message.content


    # Instantiate ALL scorers
    all_scorers = [
        AnswerRelevancyScorer(threshold=0.7),
        AnswerCorrectnessScorer(threshold=0.8),
        FaithfulnessScorer(threshold=0.8),
        InstructionAdherenceScorer(threshold=0.8),
        EmpathyScorer()
    ]

    # Run agents
    response_a = run_agent('A', user_query, [context], expected, all_scorers)
    response_b = run_agent('B', user_query, [context], expected, all_scorers)

    # Run synchronous evaluations to get scores for the UI
    def get_scores_for_ui(response_content, agent_name_suffix: str):
        # FIX: Generate a unique AND descriptive name for each evaluation run.
        unique_eval_name = f"eval_{agent_name_suffix}_{int(time.time() * 1000)}"
        
        results = judgment_client.run_evaluation(
            eval_run_name=unique_eval_name,
            examples=[Example(input=user_query, actual_output=response_content, expected_output=expected, retrieval_context=[context])],
            scorers=all_scorers,
            model="gpt-4o"
        )
        scores_dict = {}
        # FIX: The correct attribute on the result object is 'scores'.
        if results and len(results) > 0 and hasattr(results[0], 'scores') and results[0].scores:
            for scorer_run in results[0].scores:
                scores_dict[scorer_run.name] = {"score": scorer_run.score, "reason": scorer_run.reason}
        return scores_dict

    scores_a = get_scores_for_ui(response_a, "concise_agent_a")
    scores_b = get_scores_for_ui(response_b, "empathetic_agent_b")

    # Return all data to the frontend
    return jsonify({
        "context": context,
        "expected": expected,
        "agentAResponse": response_a,
        "agentBResponse": response_b,
        "agentAScores": scores_a,
        "agentBScores": scores_b
    })

if __name__ == '__main__':
    app.run(port=5001)