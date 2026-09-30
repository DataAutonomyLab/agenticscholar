import json
import argparse
from s2_paper_search import search_papers_entry


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid", type=str, default="user_id_0", help="user id")
    parser.add_argument("--kbid", type=str, default="kb_id_0", help="kb id")
    parser.add_argument("--k", type=int, default=10, help="Number of top-k paper search results returned")
    parser.add_argument("--ids", nargs="+", help="List of query_id(s) to include in evaluation.")
    return parser.parse_args()


def precision_at_k(predicted, ground_truth, k):
    predicted_k = predicted[:k]
    relevant = set(ground_truth)
    retrieved_relevant = len(set(predicted_k) & relevant)
    return retrieved_relevant / k if k > 0 else 0.0

def recall_at_k(predicted, ground_truth, k):
    relevant = set(ground_truth)
    predicted_k = predicted[:k]
    retrieved_relevant = len(set(predicted_k) & relevant)
    total_relevant = len(relevant)
    return retrieved_relevant / total_relevant if total_relevant > 0 else 0.0

def precision(predicted, ground_truth):
    relevant = set(ground_truth)
    retrieved_relevant = len(set(predicted) & relevant)
    total_retrieved = len(predicted)
    return retrieved_relevant / total_retrieved if total_retrieved > 0 else 0.0

def recall(predicted, ground_truth):
    relevant = set(ground_truth)
    retrieved_relevant = len(set(predicted) & relevant)
    total_relevant = len(relevant)
    return retrieved_relevant / total_relevant if total_relevant > 0 else 0.0


def main(args):
    user_id = args.uid
    kb_id = args.kbid

    # Load test queries from JSON file
    with open("test_data.json", "r", encoding="utf-8") as f:  # TODO: manually enter path for input queries here for testing
        test_data = json.load(f)

    # Filter by query_id if provided
    if args.ids:
        test_data = [entry for entry in test_data if entry["query_id"] in args.ids]

    # @k values for evaluation
    k_values = [1, 2, 3, 4, 5, 7, 10]

    precision_scores = []
    recall_scores = []
    precision_at_k_scores = {k: [] for k in k_values}
    recall_at_k_scores = {k: [] for k in k_values}

    detailed_results = []

    for entry in test_data:
        query_id = entry["query_id"]
        query_text = entry["query"]
        ground_truth = entry["ground_truth"]

        # Get predicted paper IDs from your search function
        predicted, results = search_papers_entry(user_id, kb_id, query_text, top_k=args.k)

        # Compute metrics
        p = precision(predicted, ground_truth)
        r = recall(predicted, ground_truth)
        precision_scores.append(p)
        recall_scores.append(r)
        
        p_at_k = {}
        r_at_k = {}
        
        for k in k_values:
            p_k = precision_at_k(predicted, ground_truth, k)
            r_k = recall_at_k(predicted, ground_truth, k)
            precision_at_k_scores[k].append(p_k)
            recall_at_k_scores[k].append(r_k)
            p_at_k[k] = p_k
            r_at_k[k] = r_k

        detailed_results.append({
            "query_id": query_id,
            "query": query_text,
            "ground_truth": ground_truth,
            "predicted": predicted,
            "results": results,
            "precision": p,
            "recall": r,
            "precision_at_k": p_at_k,
            "recall_at_k": r_at_k
        })

    # Aggregate results (mean over all queries)
    mean_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
    mean_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0

    mean_precision_at_k = {k: sum(precision_at_k_scores[k]) / len(precision_at_k_scores[k]) if precision_at_k_scores[k] else 0.0 for k in k_values}
    mean_recall_at_k = {k: sum(recall_at_k_scores[k]) / len(recall_at_k_scores[k]) if recall_at_k_scores[k] else 0.0 for k in k_values}

    summary = {
        "mean_precision": mean_precision,
        "mean_recall": mean_recall,
        "mean_precision_at_k": mean_precision_at_k,
        "mean_recall_at_k": mean_recall_at_k
    }

    print(f"Average Precision: {mean_precision:.4f}")
    print(f"Average Recall: {mean_recall:.4f}")
    for k in k_values:
        print(f"Average Precision@{k}: {mean_precision_at_k[k]:.4f}")
        print(f"Average Recall@{k}: {mean_recall_at_k[k]:.4f}")

    output_file = f"test_results-k{args.k}.json"
    with open(output_file, "w", encoding="utf-8") as f:  # TODO: manually enter path for output results here for testing
        json.dump({
            "per_query_results": detailed_results,
            "summary": summary
        }, f, indent=2)

    print(f"Evaluation complete. Results saved to {output_file}")


if __name__ == "__main__":
    args = parse_args()
    main(args)
