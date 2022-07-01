from collections import defaultdict

class PipelineManager:
    def __init__(self, state, name):
        self._state = state
        self._name = name
        self._next_id = 1
        self._nodes = {}
        self._children_map = defaultdict(set)

    def _update_hierarchy(self):
        self._children_map.clear()
        for node in self._nodes.values():
            self._children_map[node.get("parent")].add(node.get("id"))

        self.update()

    def _add_children(self, list_to_fill, node_id):
        for child_id in self._children_map[node_id]:
            node = self._nodes[child_id]
            list_to_fill.append(node)
            if node.get("collapsed"):
                continue
            self._add_children(list_to_fill, node.get("id"))

        return list_to_fill

    def update(self):
        result = self._add_children([], "0")
        new_result = sorted(result, key=lambda d: int(d["id"]))
        new_result.reverse()
        self._state[self._name] = new_result
        return new_result

    def add_nodes(self, pipelines):
        for pipeline in pipelines:
            _id = pipeline["id"]
            node = {
                **pipeline,
            }
            self._nodes[_id] = node
        self._update_hierarchy()

    def remove_node(self, _id):
        for id in self._children_map[_id]:
            self.remove_node(_id)
        self._nodes.pop(_id)
        self._update_hierarchy()

    def get_collapsed(self, id, pipeline):
        node = self.get_node(id)
        if node and node["pipeline"] == pipeline:
            return node["collapsed"]
        return True

    def toggle_collapsed(self, _id, icons=["collapsed", "collapsable"]):
        node = self.get_node(_id)
        node["collapsed"] = not node["collapsed"]

        # Toggle matching action icon
        actions = node.get("actions", [])
        for i in range(len(actions)):
            action = actions[i]
            if action in icons:
                actions[i] = icons[(icons.index(action) + 1) % 2]

        self.update()
        return node["collapsed"]

    def toggle_visible(self, _id):
        node = self.get_node(_id)
        node["visible"] = not node["visible"]
        self.update()
        return node["visible"]

    def get_visible(self, id, pipeline):
        node = self.get_node(id)
        if node and node["pipeline"] == pipeline:
            return node["visible"]
        return False

    def set_visible(self, _id, visible):
        node = self.get_node(_id)
        node["visible"] = visible
        self.update()

    def get_node(self, _id):
        return self._nodes.get(f"{_id}")
