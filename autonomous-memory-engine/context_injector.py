def inject_context(query, memories):
    context = f"Query: {query}\n\nRelevant Memories:\n"

    for memory in memories:
        context += f"- {memory}\n"

    return context
