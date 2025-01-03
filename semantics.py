from typing import Set, Dict
from pm4py.objects.dcr.extended.semantics import ExtendedSemantics
from pm4py.objects.dcr.hierarchical.obj import HierarchicalDcrGraph
class HierarchicalSemantics(ExtendedSemantics):

    # Expands a group ID into a set of sub-events
    @classmethod
    def expand_event(cls, event: str, graph: HierarchicalDcrGraph) -> Set[str]:
        if event in graph.nestedgroups:
            result = set()
            for nested_event in graph.nestedgroups[event]:
                result.update(cls.expand_event(nested_event, graph))
            return result
        return {event}

    # Expands a nested relation by creating relations to sub-events
    @classmethod
    def expand_relation(cls, relation, graph: HierarchicalDcrGraph) -> Dict[str, Set[str]]:
        expanded_relation = {}
        for src, targets in relation.items():
            expanded_src = cls.expand_event(src, graph)
            for s in expanded_src:
                if s not in expanded_relation:
                    expanded_relation[s] = set()
                for tgt in targets:
                    expanded_relation[s].update(cls.expand_event(tgt, graph))
        return expanded_relation


    # Semantics of a nested group are identical to semantics of the expanded graph
    @classmethod
    def enabled(cls, graph) -> Set[str]:
        res = set(graph.marking.included)
        expanded_conditions = cls.expand_relation(graph.conditions, graph)
        expanded_milestones = cls.expand_relation(graph.milestones, graph)

        for e in set(expanded_conditions.keys()).intersection(res):
            if len(expanded_conditions[e].intersection(graph.marking.included.difference(
                    graph.marking.executed))) > 0:
                res.discard(e)

        for e in set(expanded_milestones.keys()).intersection(res):
            if len(expanded_milestones[e].intersection(
                    graph.marking.included.intersection(graph.marking.pending))) > 0:
                res.discard(e)
        return res

    @classmethod
    def execute(cls, graph, event):
        if event in graph.marking.pending:
            graph.marking.pending.discard(event)
        graph.marking.executed.add(event)

        expanded_excludes = cls.expand_relation(graph.excludes, graph)
        expanded_includes = cls.expand_relation(graph.includes, graph)
        expanded_responses = cls.expand_relation(graph.responses, graph)

        if event in expanded_excludes:
            for e_prime in expanded_excludes[event]:
                graph.marking.included.discard(e_prime)

        if event in expanded_includes:
            for e_prime in expanded_includes[event]:
                graph.marking.included.add(e_prime)

        if event in expanded_responses:
            for e_prime in expanded_responses[event]:
                graph.marking.pending.add(e_prime)
        return graph
