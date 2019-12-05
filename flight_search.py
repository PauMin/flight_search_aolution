import os
import json
import ijson
import pandas as pd


def get_best(f):
    itinerary = pd.DataFrame(ijson.items(f, 'itinerary.item'))

    satisfactory = satisfactory_generator(f, itinerary)
    variations = [{
        'indexes': [fare['index']],
        'routes': [fare['routes']],
        'price': fare['price'],
        'weight': fare['weight']
    } for fare in next(satisfactory).iterrows()]

    found = False

    # while not found:
        # ---
    # fares = ijson.items(f, 'fares.item')
    # route = routes[0]
    # found = False
    # no_show = [fare['fid'] for fare in fares if not all(route in routes for route in fare['routes'])]
    #
    # f.seek(0, 0)
    #
    # fares = ijson.items(f, 'fares.item')
    # variations = [{
    #     'indexes': [fare['fid']],
    #     'routes': fare['routes'],
    #     'price': fare['price'],
    #     'weight': fare['price'] / len(fare['routes'])
    # } for fare in fares if route in fare['routes'] and fare['fid'] not in no_show]
    # variations = sorted(variations, key=lambda i: i['weight'])
    #
    # while not found:
    #     f.seek(0, 0)
    #     fares = ijson.items(f, 'fares.item')
    #     route = [route for route in routes if route not in variations[0]['routes']][0]
    #     satisfactory = [{
    #         'current_index': fare['fid'],
    #         'indexes': [fare['fid']],
    #         'routes': fare['routes'],
    #         'price': fare['price'],
    #         'weight': variations[0]['price'] / len(variations[0]['routes'])
    #     } for fare in fares if route in fare['routes'] and not any(route in variations[0]['routes'] for route in fare['routes']) and fare['fid'] not in no_show]
    #     satisfactory = sorted(satisfactory, key=lambda i: i['weight'])
    #
    #     variations[0]['indexes'].extend(satisfactory[0]['indexes'])
    #     variations[0]['routes'].extend(satisfactory[0]['routes'])
    #     variations[0]['price'] += satisfactory[0]['price']
    #     variations[0]['weight'] = variations[0]['price'] / len(variations[0]['routes'])
    #
    #     variations = sorted(variations, key=lambda i: i['weight'])
    #
    #     if len(variations[0]['routes']) == len(routes):
    #         found = True

    return variations[0]['indexes']


def satisfactory_generator(f, itinerary):
    for route in itinerary.iterrows():
        f.seek(0, 0)
        fares = ijson.items(f, 'fares.item')
        satisfactory = pd.DataFrame([fare for fare in fares if route[1].to_dict() in fare['routes']])
        satisfactory.drop(no_show_generator(satisfactory, itinerary), inplace=True)
        satisfactory['weight'] = satisfactory.price / len(satisfactory.routes)
        satisfactory.sort_values(by=['weight'], inplace=True)
        yield satisfactory


def no_show_generator(df, itinerary):
    for i, fare in df.iterrows():
        result = pd.Series([route in itinerary.T.to_dict().values() for route in fare['routes']]).all()
        if ~result:
            yield i


def main():
    with open(os.environ["DATA_FILE"], "r") as f:
        answer = get_best(f)

    with open(os.environ["RESULT_FILE"], 'w') as f:
        f.write(json.dumps(answer))


if __name__ == "__main__":
    main()
