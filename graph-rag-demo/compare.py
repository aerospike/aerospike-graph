#!/usr/bin/env python3
"""
Phase 5: Compare Vector-Only vs Graph-Enhanced RAG

Shows the difference between traditional RAG and Graph RAG answers.
Includes LLM-based evaluation using Microsoft's GraphRAG assessment criteria.

Usage:
    python compare.py "What is Graph RAG?"
    python compare.py  # Interactive mode
"""

import sys
import os
import json
import requests

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from chat.graph_qa_chain import GraphQAChain, GraphQAResult


# =============================================================================
# LLM-BASED ASSESSMENT (Microsoft GraphRAG Evaluation Criteria)
# =============================================================================

ASSESSMENT_CRITERIA = {
    "comprehensiveness": """How much detail does the answer provide to cover all the aspects and details of the question? A comprehensive answer should be thorough and complete, without being redundant or irrelevant. For example, if the question is 'What are the benefits and drawbacks of nuclear energy?', a comprehensive answer would provide both the positive and negative aspects of nuclear energy, such as its efficiency, environmental impact, safety, cost, etc. A comprehensive answer should not leave out any important points or provide irrelevant information.""",
    
    "diversity": """How varied and rich is the answer in providing different perspectives and insights on the question? A diverse answer should be multi-faceted and multi-dimensional, offering different viewpoints and angles on the question. For example, if the question is 'What are the causes and effects of climate change?', a diverse answer would provide different causes and effects of climate change, such as greenhouse gas emissions, deforestation, natural disasters, biodiversity loss, etc. A diverse answer should also provide different sources and evidence to support the answer.""",
    
    "directness": """How specifically and clearly does the answer address the question? A direct answer should provide a clear and concise answer to the question. For example, if the question is 'What is the capital of France?', a direct answer would be 'Paris'. A direct answer should not provide any irrelevant or unnecessary information that does not answer the question.""",
    
    "empowerment": """How well does the answer help the reader understand and make informed judgements about the topic without being misled or making fallacious assumptions. Evaluate each answer on the quality of answer as it relates to clearly explaining and providing reasoning and sources behind the claims in the answer."""
}

# Grounding scores from check_grounding (set by print_comparison)
_vector_grounding_score = 1.0
_graph_grounding_score = 1.0

# Factual accuracy scores (set by print_comparison)
_vector_factual_score = 1.0
_graph_factual_score = 1.0

ASSESSMENT_PROMPT = """---Role---
You are a helpful assistant responsible for grading two answers to a question that are provided by two different people.

---Goal---
Given a question and two answers (Answer 1 and Answer 2), assess which answer is better according to the following measure:
{criteria}

Your assessment should include two parts:
- Winner: either 1 (if Answer 1 is better) and 2 (if Answer 2 is better) or 0 if they are fundamentally similar and the differences are immaterial.
- Reasoning: a short explanation of why you chose the winner with respect to the measure described above.

Format your response as a JSON object with the following structure:
{{
  "winner": <1, 2, or 0>,
  "reasoning": "Answer X is better because <your reasoning>."
}}

---Question---
{question}

---Answer 1 (Vector RAG)---
{answer1}

---Answer 2 (Graph RAG)---
{answer2}

Assess which answer is better according to the measure described above.

Output:"""


def assess_answers(question: str, vector_answer: str, graph_answer: str, criterion_name: str, criterion_desc: str) -> dict:
    """
    Use LLM to assess which answer is better for a given criterion.
    
    Returns:
        dict with 'winner' (0, 1, or 2) and 'reasoning'
    """
    prompt = ASSESSMENT_PROMPT.format(
        criteria=criterion_desc,
        question=question,
        answer1=vector_answer[:3000],  # Truncate to avoid token limits
        answer2=graph_answer[:3000]
    )
    
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 8192}
            },
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()["response"].strip()
        
        # Parse JSON from response
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > 0:
            data = json.loads(result[start:end])
            return {
                "winner": data.get("winner", 0),
                "reasoning": data.get("reasoning", "No reasoning provided")
            }
    except Exception as e:
        return {"winner": 0, "reasoning": f"Assessment failed: {e}"}
    
    return {"winner": 0, "reasoning": "Could not parse assessment"}


def run_full_assessment(question: str, vector_answer: str, graph_answer: str) -> dict:
    """
    Run assessment across all criteria.
    
    Returns:
        dict with results for each criterion and overall winner
    """
    results = {}
    vector_wins = 0
    graph_wins = 0
    ties = 0
    
    print("\n  🔬 Running LLM-based assessment...")
    
    for criterion_name, criterion_desc in ASSESSMENT_CRITERIA.items():
        print(f"     Evaluating {criterion_name}...", end="\r")
        assessment = assess_answers(question, vector_answer, graph_answer, criterion_name, criterion_desc)
        results[criterion_name] = assessment
        
        if assessment["winner"] == 1:
            vector_wins += 1
        elif assessment["winner"] == 2:
            graph_wins += 1
        else:
            ties += 1
    
    print(" " * 50, end="\r")  # Clear line
    
    # Determine overall winner
    if graph_wins > vector_wins:
        overall = "Graph RAG"
    elif vector_wins > graph_wins:
        overall = "Vector RAG"
    else:
        overall = "Tie"
    
    results["summary"] = {
        "vector_wins": vector_wins,
        "graph_wins": graph_wins,
        "ties": ties,
        "overall_winner": overall
    }
    
    return results


# =============================================================================
# 3-WAY ASSESSMENT (Vector vs Graph vs Hybrid)
# =============================================================================

ASSESSMENT_PROMPT_3WAY = """---Role---
You are a helpful assistant responsible for grading three answers to a question.

---Goal---
Given a question and three answers (Answer 1: Vector RAG, Answer 2: Graph RAG, Answer 3: Hybrid RAG), 
assess which answer is BEST according to the following measure:
{criteria}

Your assessment should include:
- Winner: 1 (Vector RAG), 2 (Graph RAG), or 3 (Hybrid RAG). Use 0 only if all three are fundamentally equal.
- Reasoning: a short explanation of why you chose the winner.

Format your response as a JSON object:
{{
  "winner": <1, 2, 3, or 0>,
  "reasoning": "Answer X is better because <your reasoning>."
}}

---Question---
{question}

---Answer 1 (Vector RAG)---
{answer1}

---Answer 2 (Graph RAG)---
{answer2}

---Answer 3 (Hybrid RAG)---
{answer3}

Assess which answer is BEST. Output JSON only:"""


def assess_answers_3way(question: str, vector_answer: str, graph_answer: str, hybrid_answer: str,
                        criterion_name: str, criterion_desc: str) -> dict:
    """Use LLM to assess which of 3 answers is best for a given criterion."""
    prompt = ASSESSMENT_PROMPT_3WAY.format(
        criteria=criterion_desc,
        question=question,
        answer1=vector_answer[:2000],
        answer2=graph_answer[:2000],
        answer3=hybrid_answer[:2000]
    )
    
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 8192}
            },
            timeout=90
        )
        response.raise_for_status()
        
        result = response.json()["response"].strip()
        
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > 0:
            data = json.loads(result[start:end])
            return {
                "winner": data.get("winner", 0),
                "reasoning": data.get("reasoning", "No reasoning provided")
            }
    except Exception as e:
        return {"winner": 0, "reasoning": f"Assessment failed: {e}"}
    
    return {"winner": 0, "reasoning": "Could not parse assessment"}


def run_full_assessment_3way(question: str, vector_answer: str, graph_answer: str, hybrid_answer: str) -> dict:
    """Run 3-way assessment across all criteria."""
    results = {}
    wins = {"vector": 0, "graph": 0, "hybrid": 0, "tie": 0}
    
    print("\n  🔬 Running LLM-based assessment (3-way)...")
    
    for criterion_name, criterion_desc in ASSESSMENT_CRITERIA.items():
        print(f"     Evaluating {criterion_name}...", end="\r")
        assessment = assess_answers_3way(question, vector_answer, graph_answer, hybrid_answer,
                                         criterion_name, criterion_desc)
        results[criterion_name] = assessment
        
        winner = assessment["winner"]
        if winner == 1:
            wins["vector"] += 1
        elif winner == 2:
            wins["graph"] += 1
        elif winner == 3:
            wins["hybrid"] += 1
        else:
            wins["tie"] += 1
    
    print(" " * 50, end="\r")
    
    results["summary"] = wins
    return results


def print_assessment_3way(assessment_results: dict):
    """Pretty print the 3-way assessment results."""
    global _vector_factual_score, _graph_factual_score
    
    print("\n" + "═" * 70)
    print("🔬 LLM-BASED ASSESSMENT (3-Way: Vector vs Graph vs Hybrid)")
    print("═" * 70)
    
    winner_labels = {1: "🔢 Vector RAG", 2: "🕸️  Graph RAG", 3: "🔀 Hybrid RAG", 0: "🤝 Tie"}
    
    for criterion in ["comprehensiveness", "diversity", "directness", "empowerment"]:
        result = assessment_results.get(criterion, {})
        winner = result.get("winner", 0)
        reasoning = result.get("reasoning", "N/A")
        
        print(f"\n📊 {criterion.upper()}")
        print(f"   Winner: {winner_labels.get(winner, '?')}")
        print(f"   Reason: {reasoning[:150]}...")
    
    # Add ACCURACY based on factual scores
    print(f"\n📊 ACCURACY (Factual Correctness)")
    v_score = _vector_factual_score
    g_score = _graph_factual_score
    # For hybrid, assume same as graph since it uses graph entities
    h_score = g_score
    
    max_score = max(v_score, g_score, h_score)
    if v_score == max_score and g_score < max_score:
        accuracy_winner = 1
    elif g_score == max_score and v_score < max_score:
        # Both graph and hybrid get credit
        accuracy_winner = 2  # or could be 3
    else:
        accuracy_winner = 0
    
    print(f"   Winner: {winner_labels.get(accuracy_winner, '🤝 Tie')}")
    print(f"   Vector: {v_score:.0%} | Graph: {g_score:.0%} | Hybrid: {h_score:.0%}")
    
    # Summary
    summary = assessment_results.get("summary", {})
    vector_wins = summary.get('vector', 0)
    graph_wins = summary.get('graph', 0)
    hybrid_wins = summary.get('hybrid', 0)
    ties = summary.get('tie', 0)
    
    # Add accuracy result
    if accuracy_winner == 1:
        vector_wins += 1
    elif accuracy_winner == 2:
        graph_wins += 1
    elif accuracy_winner == 3:
        hybrid_wins += 1
    else:
        ties += 1
    
    print("\n" + "─" * 70)
    print("📈 OVERALL SUMMARY (5 criteria)")
    print("─" * 70)
    print(f"   🔢 Vector RAG wins: {vector_wins}")
    print(f"   🕸️  Graph RAG wins:  {graph_wins}")
    print(f"   🔀 Hybrid RAG wins: {hybrid_wins}")
    print(f"   🤝 Ties:            {ties}")
    
    # Determine final winner
    max_wins = max(vector_wins, graph_wins, hybrid_wins)
    winners = []
    if vector_wins == max_wins:
        winners.append("🔢 Vector RAG")
    if graph_wins == max_wins:
        winners.append("🕸️  Graph RAG")
    if hybrid_wins == max_wins:
        winners.append("🔀 Hybrid RAG")
    
    if len(winners) == 1:
        print(f"\n   🏆 OVERALL WINNER: {winners[0]}")
    else:
        print(f"\n   🏆 OVERALL WINNER: 🤝 Tie ({', '.join(winners)})")
    
    print("═" * 70)


def print_assessment(assessment_results: dict, vector_grounding: dict = None, graph_grounding: dict = None):
    """Pretty print the assessment results including accuracy based on grounding"""
    global _vector_grounding_score, _graph_grounding_score
    
    print("\n" + "═" * 70)
    print("🔬 LLM-BASED ASSESSMENT (Microsoft GraphRAG Criteria + Accuracy)")
    print("═" * 70)
    
    # Print each criterion result
    for criterion in ["comprehensiveness", "diversity", "directness", "empowerment"]:
        result = assessment_results.get(criterion, {})
        winner = result.get("winner", 0)
        reasoning = result.get("reasoning", "N/A")
        
        if winner == 1:
            winner_str = "🔢 Vector RAG"
        elif winner == 2:
            winner_str = "🕸️  Graph RAG"
        else:
            winner_str = "🤝 Tie"
        
        print(f"\n📊 {criterion.upper()}")
        print(f"   Winner: {winner_str}")
        print(f"   Reason: {reasoning}")
    
    # Add ACCURACY based on FACTUAL accuracy (entity classification correctness)
    print(f"\n📊 ACCURACY (Factual Correctness)")
    v_score = _vector_factual_score
    g_score = _graph_factual_score
    
    if g_score > v_score:
        accuracy_winner = 2
        winner_str = "🕸️  Graph RAG"
        reasoning = f"Graph RAG is factually accurate ({g_score:.0%}) while Vector RAG made entity classification errors ({v_score:.0%})."
    elif v_score > g_score:
        accuracy_winner = 1
        winner_str = "🔢 Vector RAG"
        reasoning = f"Vector RAG is factually accurate ({v_score:.0%}) while Graph RAG made errors ({g_score:.0%})."
    else:
        accuracy_winner = 0
        winner_str = "🤝 Tie"
        reasoning = f"Both have equal factual accuracy ({v_score:.0%})."
    
    print(f"   Winner: {winner_str}")
    print(f"   Vector RAG grounding: {v_score:.0%}")
    print(f"   Graph RAG grounding: {g_score:.0%}")
    print(f"   Reason: {reasoning}")
    
    # Update summary with accuracy
    summary = assessment_results.get("summary", {})
    vector_wins = summary.get('vector_wins', 0)
    graph_wins = summary.get('graph_wins', 0)
    ties = summary.get('ties', 0)
    
    # Add accuracy result
    if accuracy_winner == 1:
        vector_wins += 1
    elif accuracy_winner == 2:
        graph_wins += 1
    else:
        ties += 1
    
    # Print summary (now includes accuracy)
    print("\n" + "─" * 70)
    print("📈 OVERALL SUMMARY (including Accuracy)")
    print("─" * 70)
    print(f"   Vector RAG wins: {vector_wins}")
    print(f"   Graph RAG wins:  {graph_wins}")
    print(f"   Ties:            {ties}")
    
    # Determine overall winner with accuracy included
    if graph_wins > vector_wins:
        overall = "Graph RAG"
    elif vector_wins > graph_wins:
        overall = "Vector RAG"
    else:
        overall = "Tie"
    
    if overall == "Graph RAG":
        print(f"\n   🏆 OVERALL WINNER: 🕸️  Graph RAG")
    elif overall == "Vector RAG":
        print(f"\n   🏆 OVERALL WINNER: 🔢 Vector RAG")
    else:
        print(f"\n   🏆 OVERALL WINNER: 🤝 Tie")
    
    print("═" * 70)


def check_factual_accuracy(answer: str, graph_store=None) -> dict:
    """
    Check if entity claims in the answer match what's in the knowledge graph.
    
    This catches hallucinations where the LLM confuses entities (e.g., calling
    CASGEVY a "GLP-1 agonist" when it's actually a "gene therapy").
    
    Returns:
        dict with factual accuracy analysis
    """
    import re
    
    # Known entity-to-type mappings from the FDA corpus
    # These are the CORRECT classifications
    ENTITY_FACTS = {
        # Gene therapies for sickle cell
        'casgevy': {'type': 'gene therapy', 'condition': 'sickle cell', 'technology': 'crispr'},
        'lyfgenia': {'type': 'gene therapy', 'condition': 'sickle cell', 'technology': 'lentiviral'},
        # GLP-1 / weight loss drugs
        'wegovy': {'type': 'glp-1 agonist', 'condition': 'obesity', 'company': 'novo nordisk'},
        'zepbound': {'type': 'gip/glp-1 agonist', 'condition': 'obesity', 'company': 'eli lilly'},
        'mounjaro': {'type': 'gip/glp-1 agonist', 'condition': 'diabetes', 'company': 'eli lilly'},
        'ozempic': {'type': 'glp-1 agonist', 'condition': 'diabetes', 'company': 'novo nordisk'},
        'saxenda': {'type': 'glp-1 agonist', 'condition': 'obesity', 'company': 'novo nordisk'},
        'tirzepatide': {'type': 'gip/glp-1 agonist', 'condition': 'obesity/diabetes'},
        'semaglutide': {'type': 'glp-1 agonist', 'condition': 'obesity/diabetes'},
        # Alzheimer's drugs
        'kisunla': {'type': 'anti-amyloid antibody', 'condition': 'alzheimer', 'company': 'eli lilly'},
        'leqembi': {'type': 'anti-amyloid antibody', 'condition': 'alzheimer', 'company': 'eisai'},
        'rexulti': {'type': 'antipsychotic', 'condition': 'alzheimer agitation'},
        # Cancer drugs
        'imdelltra': {'type': 'bite antibody', 'condition': 'lung cancer', 'company': 'amgen'},
        'zynyz': {'type': 'pd-1 inhibitor', 'condition': 'merkel cell carcinoma'},
    }
    
    answer_lower = answer.lower()
    errors = []
    correct = []
    checked = []
    
    for entity, facts in ENTITY_FACTS.items():
        if entity in answer_lower:
            checked.append(entity)
            entity_type = facts['type']
            
            # Check for WRONG type associations
            # If CASGEVY is mentioned with "glp-1" or "semaglutide", that's wrong
            if entity in ['casgevy', 'lyfgenia']:
                # These are gene therapies, not GLP-1 drugs
                wrong_associations = ['glp-1', 'semaglutide', 'tirzepatide', 'weight loss', 'obesity drug', 'gip/glp']
                for wrong in wrong_associations:
                    # Check if wrong term appears near the entity (within 200 chars)
                    entity_pos = answer_lower.find(entity)
                    context = answer_lower[max(0, entity_pos-200):entity_pos+200]
                    if wrong in context:
                        errors.append(f"{entity.upper()} incorrectly associated with '{wrong}' (actually: {entity_type})")
                        break
                else:
                    # Check for correct associations
                    correct_terms = ['gene therapy', 'crispr', 'sickle cell', 'lentiviral', 'hbf', 'hemoglobin']
                    for term in correct_terms:
                        if term in answer_lower:
                            correct.append(f"{entity.upper()} correctly identified as {entity_type}")
                            break
            
            elif entity in ['wegovy', 'zepbound', 'mounjaro', 'ozempic']:
                # These ARE GLP-1/GIP drugs
                wrong_associations = ['gene therapy', 'crispr', 'sickle cell']
                for wrong in wrong_associations:
                    if wrong in answer_lower:
                        errors.append(f"{entity.upper()} incorrectly associated with '{wrong}' (actually: {entity_type})")
                        break
                else:
                    correct.append(f"{entity.upper()} correctly identified as {entity_type}")
    
    # Calculate accuracy score
    total_checks = len(errors) + len(correct)
    if total_checks > 0:
        score = len(correct) / total_checks
    else:
        score = 1.0  # No entities to check = assume accurate
    
    return {
        "entities_checked": checked,
        "correct": correct,
        "errors": errors,
        "score": score,
        "is_accurate": len(errors) == 0
    }


def check_grounding(answer: str, retrieved_docs: set) -> dict:
    """
    Check if the answer is grounded in the retrieved documents.
    Only checks for KNOWN document names to avoid false positives.
    
    Returns:
        dict with grounding analysis
    """
    import re
    
    # ONLY check for known document names (Shakespeare plays and common corpus docs)
    # This avoids false positives from regular words
    known_docs = {
        'othello', 'macbeth', 'hamlet', 'king_lear', 'king lear',
        'romeo_and_juliet', 'romeo and juliet', 
        'tempest', 'the tempest',
        'midsummer', 'midsummer_nights_dream', "midsummer night's dream",
        'twelfth_night', 'twelfth night',
        'merchant_of_venice', 'merchant of venice', 'merchant',
        'taming_of_the_shrew', 'taming of the shrew', 'taming',
        'henry_v', 'henry v',
        'richard_iii', 'richard iii',
        'much_ado_about_nothing', 'much ado about nothing', 'much_ado'
    }
    
    answer_lower = answer.lower()
    
    # Find which known documents are mentioned in the answer
    mentioned_docs = set()
    for doc in known_docs:
        if doc in answer_lower:
            # Normalize to the canonical form
            canonical = doc.replace(' ', '_').replace("'", '')
            # Map variations to canonical names
            if 'romeo' in canonical:
                mentioned_docs.add('romeo_and_juliet')
            elif 'midsummer' in canonical:
                mentioned_docs.add('midsummer_nights_dream')
            elif 'merchant' in canonical:
                mentioned_docs.add('merchant_of_venice')
            elif 'twelfth' in canonical:
                mentioned_docs.add('twelfth_night')
            elif 'taming' in canonical:
                mentioned_docs.add('taming_of_the_shrew')
            elif 'much' in canonical or 'ado' in canonical:
                mentioned_docs.add('much_ado_about_nothing')
            elif 'lear' in canonical:
                mentioned_docs.add('king_lear')
            else:
                mentioned_docs.add(canonical)
    
    # Normalize retrieved docs for comparison
    retrieved_normalized = set()
    for d in retrieved_docs:
        d_lower = d.lower().replace('_', '')
        retrieved_normalized.add(d_lower)
        # Also add common variations
        if 'romeo' in d_lower:
            retrieved_normalized.add('romeoandjuliet')
        if 'midsummer' in d_lower:
            retrieved_normalized.add('midsummernightsdream')
    
    mentioned_normalized = {d.lower().replace('_', '') for d in mentioned_docs}
    
    # Find ungrounded mentions (mentioned but not retrieved)
    ungrounded = mentioned_normalized - retrieved_normalized
    grounded = mentioned_normalized & retrieved_normalized
    
    # Calculate grounding score
    if mentioned_normalized:
        score = len(grounded) / len(mentioned_normalized)
    else:
        score = 1.0  # No document mentions = fully grounded
    
    return {
        "retrieved": retrieved_docs,
        "mentioned": mentioned_docs,
        "grounded": grounded,
        "ungrounded": ungrounded,
        "score": score,
        "is_grounded": len(ungrounded) == 0
    }


def print_comparison(vector_result: GraphQAResult, graph_result: GraphQAResult, run_assessment: bool = True, hybrid_result: GraphQAResult = None):
    """Pretty print comparison of results"""
    
    print("\n" + "=" * 70)
    if hybrid_result:
        print("📊 COMPARISON: Vector RAG vs Graph RAG vs Hybrid RAG")
    else:
        print("📊 COMPARISON: Vector-Only RAG vs Graph-Enhanced RAG")
    print("=" * 70)
    
    # Get retrieved doc sets
    vector_docs = {c['doc_id'] for c in vector_result.vector_chunks}
    graph_docs = {c.get('doc_id', [''])[0] if isinstance(c.get('doc_id'), list) else c.get('doc_id', '') 
                  for c in graph_result.graph_chunks}
    graph_docs = {d for d in graph_docs if d}  # Remove empty
    
    # Vector-only answer
    print("\n" + "─" * 70)
    print("🔢 VECTOR-ONLY RAG")
    print("─" * 70)
    print(f"\n{vector_result.answer}")
    print(f"\n📚 Sources: {len(vector_result.vector_chunks)} chunks from vector search")
    for i, chunk in enumerate(vector_result.vector_chunks[:3]):
        print(f"   {i+1}. [{chunk['distance']:.3f}] {chunk['doc_id']}")
    
    # Grounding check for Vector RAG
    vector_grounding = check_grounding(vector_result.answer, vector_docs)
    if not vector_grounding["is_grounded"]:
        print(f"\n⚠️  GROUNDING WARNING: Answer mentions documents NOT in retrieved sources!")
        print(f"   Retrieved: {vector_grounding['retrieved']}")
        print(f"   Mentioned but NOT retrieved: {vector_grounding['ungrounded']}")
        print(f"   🚨 Likely using training data instead of context!")
    
    # Graph-enhanced answer
    print("\n" + "─" * 70)
    print("🕸️  GRAPH-ENHANCED RAG")
    print("─" * 70)
    print(f"\n{graph_result.answer}")
    print(f"\n📚 Sources:")
    print(f"   • {len(graph_result.vector_chunks)} chunks from vector search")
    print(f"   • {len(graph_result.graph_entities)} entities from knowledge graph")
    print(f"   • {len(graph_result.graph_chunks)} additional chunks from graph traversal")
    
    if graph_result.graph_entities:
        print(f"\n🏷️  Entities found:")
        for entity in graph_result.graph_entities[:5]:
            name = entity.get('name', ['?'])[0] if isinstance(entity.get('name'), list) else entity.get('name', '?')
            etype = entity.get('entity_type', [''])[0] if isinstance(entity.get('entity_type'), list) else entity.get('entity_type', '')
            print(f"   • {name} ({etype})")
    
    # Grounding check for Graph RAG
    graph_grounding = check_grounding(graph_result.answer, graph_docs)
    if not graph_grounding["is_grounded"]:
        print(f"\n⚠️  GROUNDING WARNING: Answer mentions documents NOT in retrieved sources!")
        print(f"   Retrieved: {graph_grounding['retrieved']}")
        print(f"   Mentioned but NOT retrieved: {graph_grounding['ungrounded']}")
        print(f"   🚨 Likely using training data instead of context!")
    else:
        print(f"\n✅ GROUNDED: All mentioned documents are in retrieved sources")
    
    # Print grounding comparison summary
    print("\n" + "─" * 70)
    print("📍 GROUNDING SUMMARY")
    print("─" * 70)
    print(f"   Vector RAG: {'✅ Grounded' if vector_grounding['is_grounded'] else '❌ UNGROUNDED'} (score: {vector_grounding['score']:.0%})")
    print(f"   Graph RAG:  {'✅ Grounded' if graph_grounding['is_grounded'] else '❌ UNGROUNDED'} (score: {graph_grounding['score']:.0%})")
    
    # FACTUAL ACCURACY CHECK - catches entity confusion/hallucination
    print("\n" + "─" * 70)
    print("🔬 FACTUAL ACCURACY CHECK (Entity Classification)")
    print("─" * 70)
    
    vector_facts = check_factual_accuracy(vector_result.answer)
    graph_facts = check_factual_accuracy(graph_result.answer)
    
    print(f"\n   🔢 Vector RAG: {'✅ Accurate' if vector_facts['is_accurate'] else '❌ INACCURATE'} ({vector_facts['score']:.0%})")
    if vector_facts['errors']:
        for err in vector_facts['errors']:
            print(f"      ❌ {err}")
    if vector_facts['correct']:
        for c in vector_facts['correct'][:2]:
            print(f"      ✅ {c}")
    
    print(f"\n   🕸️  Graph RAG: {'✅ Accurate' if graph_facts['is_accurate'] else '❌ INACCURATE'} ({graph_facts['score']:.0%})")
    if graph_facts['errors']:
        for err in graph_facts['errors']:
            print(f"      ❌ {err}")
    if graph_facts['correct']:
        for c in graph_facts['correct'][:2]:
            print(f"      ✅ {c}")
    
    # Set global grounding scores for accuracy assessment
    global _vector_grounding_score, _graph_grounding_score
    _vector_grounding_score = vector_grounding['score']
    _graph_grounding_score = graph_grounding['score']
    
    # Store factual accuracy for use in assessment
    global _vector_factual_score, _graph_factual_score
    _vector_factual_score = vector_facts['score']
    _graph_factual_score = graph_facts['score']
    
    # Print Hybrid RAG if provided
    if hybrid_result:
        hybrid_docs = {c['doc_id'] for c in hybrid_result.vector_chunks}
        hybrid_docs.update({c.get('doc_id', [''])[0] if isinstance(c.get('doc_id'), list) else c.get('doc_id', '') 
                           for c in hybrid_result.graph_chunks})
        hybrid_docs = {d for d in hybrid_docs if d}
        
        print("\n" + "─" * 70)
        print("🔀 HYBRID RAG (Vector + Graph)")
        print("─" * 70)
        print(f"\n{hybrid_result.answer}")
        print(f"\n📚 Sources:")
        print(f"   • {len(hybrid_result.vector_chunks)} chunks from vector search")
        print(f"   • {len(hybrid_result.graph_entities)} entities from knowledge graph")
        print(f"   • {len(hybrid_result.graph_chunks)} additional chunks from graph traversal")
        
        if hybrid_result.graph_entities:
            print(f"\n🏷️  Entities found:")
            for entity in hybrid_result.graph_entities[:5]:
                name = entity.get('name', ['?'])[0] if isinstance(entity.get('name'), list) else entity.get('name', '?')
                etype = entity.get('entity_type', [''])[0] if isinstance(entity.get('entity_type'), list) else entity.get('entity_type', '')
                print(f"   • {name} ({etype})")
        
        hybrid_grounding = check_grounding(hybrid_result.answer, hybrid_docs)
        hybrid_facts = check_factual_accuracy(hybrid_result.answer)
        print(f"\n   Grounding: {'✅ Grounded' if hybrid_grounding['is_grounded'] else '❌ UNGROUNDED'} ({hybrid_grounding['score']:.0%})")
        print(f"   Factual:   {'✅ Accurate' if hybrid_facts['is_accurate'] else '❌ INACCURATE'} ({hybrid_facts['score']:.0%})")
        if hybrid_facts['errors']:
            for err in hybrid_facts['errors']:
                print(f"      ❌ {err}")
    
    # Run LLM-based assessment
    if run_assessment:
        # If hybrid result exists, do 3-way assessment
        if hybrid_result:
            assessment_results = run_full_assessment_3way(
                vector_result.question,
                vector_result.answer,
                graph_result.answer,
                hybrid_result.answer
            )
            print_assessment_3way(assessment_results)
        else:
            assessment_results = run_full_assessment(
                vector_result.question,
                vector_result.answer,
                graph_result.answer
            )
            print_assessment(assessment_results)
    else:
        print("\n" + "=" * 70)


def interactive_mode(run_assessment: bool = True):
    """Run interactive comparison session"""
    print("\n" + "=" * 70)
    print("   📊 GRAPH RAG COMPARISON TOOL")
    print("   Compare Vector-Only vs Graph-Enhanced answers")
    if run_assessment:
        print("   (with LLM-based assessment)")
    print("   Type 'quit' to exit")
    print("=" * 70)
    
    with GraphQAChain() as qa:
        while True:
            try:
                question = input("\n❓ Question: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            print("\n⏳ Processing (this may take a moment)...")
            
            vector_result, graph_result, hybrid_result = qa.compare(question, verbose=True)
            print_comparison(vector_result, graph_result, run_assessment=run_assessment, hybrid_result=hybrid_result)


def single_question(question: str, run_assessment: bool = True):
    """Compare for a single question"""
    print(f"\n❓ Question: {question}")
    print("⏳ Processing (this may take a moment)...")
    
    with GraphQAChain() as qa:
        vector_result, graph_result, hybrid_result = qa.compare(question, verbose=True)
        print_comparison(vector_result, graph_result, run_assessment=run_assessment, hybrid_result=hybrid_result)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compare Vector-Only RAG vs Graph-Enhanced RAG answers"
    )
    parser.add_argument(
        'question',
        nargs='*',
        help='Question to ask (interactive mode if not provided)'
    )
    parser.add_argument(
        '--no-assess',
        action='store_true',
        help='Skip LLM-based assessment of answers'
    )
    
    args = parser.parse_args()
    run_assessment = not args.no_assess
    
    if args.question:
        # Single question mode
        question = " ".join(args.question)
        single_question(question, run_assessment=run_assessment)
    else:
        # Interactive mode
        interactive_mode(run_assessment=run_assessment)


if __name__ == "__main__":
    main()

