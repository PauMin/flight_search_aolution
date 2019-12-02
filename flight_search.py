import os
import json
import time
import pandas as pd


def find_optimal_combination(data):
    # Get itinerary and fares to separate dictionaries
    itinerary = data['itinerary']
    fares = data['fares']

    # Convert data frames
    df_fares = pd.DataFrame.from_dict(fares).set_index('fid')

    # Exclude no show fares
    no_show = [i for i in no_show_generator(df_fares, itinerary)]
    df_fares.drop(no_show, inplace=True)

    # Put weights on fares and sort them
    df_fares['weight'] = [len(fare[1].routes) / fare[1].price for fare in df_fares.iterrows()]
    df_fares.sort_values(by=['weight'], inplace=True)

    # Drop duplicate fares with higher weight
    df_fares["t_routes"] = df_fares.routes.apply(lambda x: tuple(json.dumps(x)))
    df_fares.drop_duplicates(subset='t_routes', keep='first')

    start = time.time()
    # Find variations
    best = get_best(df_fares, itinerary)
    finish = time.time()

    print(finish - start)

    return best


def no_show_generator(df, itinerary):
    for i, fare in df.iterrows():
        result = pd.Series([route in itinerary for route in fare['routes']]).all()
        if ~result:
            yield i


def get_best(df, itinerary):
    variations = []
    best = {}
    found = False
    route = itinerary[0]
    satisfactory = df[[route in fare for fare in df.routes]]
    df.drop(satisfactory.index, inplace=True)
    variations.extend(
        [{
            'indexes': [fare[0]],
            'routes': fare[1].routes,
            'price': fare[1].price,
            'weight': fare[1].weight
        } for fare in satisfactory.iterrows()]
    )

    while not found:
        route = [route for route in itinerary if route not in variations[0]['routes']][0]
        satisfactory = df[[route in fare for fare in df.routes]]
        df.drop(satisfactory.index, inplace=True)
        fill = satisfactory.iloc[0]

        variations[0]['indexes'].append(satisfactory.first_valid_index())
        variations[0]['routes'].extend(fill.routes)
        variations[0]['price'] += fill.price
        variations[0]['weight'] = len(fill.routes) / fill.price

        best = variations[0]
        variations = sorted(variations, key=lambda i: i['weight'])

        if best['indexes'] == variations[0]['indexes'] and best['routes']:
            found = True
            continue

    return best['indexes']


def main():
    with open(os.environ["DATA_FILE"], "r") as f:
        data = json.loads(f.read())

    answer = find_optimal_combination(data)

    with open(os.environ["RESULT_FILE"], 'w') as f:
        f.write(json.dumps(answer))


if __name__ == "__main__":
    main()
