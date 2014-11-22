from kivy.storage.jsonstore import JsonStore

store = JsonStore("word_lists.json")
print store.get("test")["m"]


