from kivy.storage.jsonstore import JsonStore

store = JsonStore('hello.json')

# put some values
#store.put('tito', mylist = ["tito", "sucks", "balls"])


# get a value using a index key and key
print('tito is', store.get('joe')['mylist'])

# or guess the key/entry for a part of the key
# for item in store.find(name='Gabriel'):
#     print('tshirtmans index key is', item[0])
#     print('his key value pairs are', str(item[1]))