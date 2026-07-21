"""
Harnais d'évaluation du RAG — Phase 7.

Mesure objectivement la qualité du pipeline (retrieval + génération),
plutôt que de se fier à des tests manuels ponctuels. Basé sur des
questions dont on connaît la bonne réponse attendue (vérité terrain),
construites à partir de vraies observations faites en testant le système.
"""

import json
from pathlib import Path

from src.rag.retrieval import search
from src.agents.customer_service_agent import answer_question
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Vérité terrain : chaque cas précise ce qu'on attend vraiment.
# "expected_product" = None signifie qu'on attend un refus honnête
# (garde-fou anti-hallucination), pas une invention de réponse.
TEST_CASES = [
    {
        "question": "Avez-vous du lait sans lactose ?",
        "expected_product": "Lait sans lactose",
    },
    {
        "question": "Je cherche une boisson au cola",
        "expected_product": "Coca-Cola",
    },
    {
        "question": "Quels produits contiennent des cacahuètes ?",
        "expected_product": "Be Nuts",
    },
    {
        "question": "Avez-vous des pneus de voiture ?",
        "expected_product": None,  # ↑ aucun produit de ce type dans un supermarché alimentaire
    },
]


def evaluate_retrieval(question: str, expected_product: str | None) -> bool:
    """Le produit attendu apparaît-il parmi les chunks retrouvés par le retrieval ?"""
    if expected_product is None:
        return True  # rien n'est attendu, pas de vérification à faire ici

    chunks = search(question)
    found_names = [c.metadata.get("product_name", "") for c in chunks]
    return any(expected_product.lower() in name.lower() for name in found_names)


def evaluate_answer(question: str, expected_product: str | None) -> tuple[bool, str]:
    """La réponse finale mentionne-t-elle le bon produit (ou refuse-t-elle
    honnêtement si aucun produit n'est attendu) ?"""
    answer_text, sources = answer_question(question)

    if expected_product is None:
        # ↑ on attend un refus, PAS une liste de produits inventés
        refusal_markers = ["désolé", "n'ai pas", "ne peux pas", "n'ai trouvé"]
        is_honest_refusal = any(marker in answer_text.lower() for marker in refusal_markers)
        return is_honest_refusal, answer_text

    mentioned = expected_product.lower() in answer_text.lower() or any(
        expected_product.lower() in s.lower() for s in sources
    )
    return mentioned, answer_text


def run_evaluation() -> dict:
    """Lance tous les cas de test et calcule les métriques agrégées."""
    results = []

    for case in TEST_CASES:
        question = case["question"]
        expected = case["expected_product"]

        retrieval_ok = evaluate_retrieval(question, expected)
        answer_ok, answer_text = evaluate_answer(question, expected)

        results.append({
            "question": question,
            "expected_product": expected,
            "retrieval_hit": retrieval_ok,
            "answer_correct": answer_ok,
            "answer_preview": answer_text[:150],
        })

        status = "✅" if (retrieval_ok and answer_ok) else "❌"
        logger.info("%s '%s' — retrieval=%s, réponse=%s", status, question, retrieval_ok, answer_ok)

    total = len(results)
    retrieval_score = sum(r["retrieval_hit"] for r in results) / total
    answer_score = sum(r["answer_correct"] for r in results) / total

    report = {
        "total_cases": total,
        "retrieval_recall": round(retrieval_score, 2),
        "answer_accuracy": round(answer_score, 2),
        "details": results,
    }
    return report


def save_report(report: dict, path: str = "eval_report.json") -> None:
    Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Rapport sauvegardé : %s", path)


if __name__ == "__main__":
    report = run_evaluation()

    print(f"\n{'='*50}")
    print(f"RAPPORT D'ÉVALUATION")
    print(f"{'='*50}")
    print(f"Cas testés          : {report['total_cases']}")
    print(f"Retrieval recall     : {report['retrieval_recall']*100:.0f}%")
    print(f"Answer accuracy       : {report['answer_accuracy']*100:.0f}%")
    print(f"{'='*50}\n")

    for r in report["details"]:
        status = "✅" if (r["retrieval_hit"] and r["answer_correct"]) else "❌"
        print(f"{status} {r['question']}")
        if not (r["retrieval_hit"] and r["answer_correct"]):
            print(f"   Attendu : {r['expected_product']}")
            print(f"   Réponse : {r['answer_preview']}...")

    save_report(report)