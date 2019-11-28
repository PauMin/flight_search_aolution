import os
import json
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

    # Find variations
    variations = get_variations(df_fares, itinerary)

    # Get cheapest variation
    profitable = min(variations, key=lambda x: x['price'])

    return profitable['fares']


def no_show_generator(df, itinerary):
    for i, fare in df.iterrows():
        result = pd.Series([route in itinerary for route in fare['routes']]).all()
        if ~result:
            yield i


def get_variations(df, itinerary):
    routes = itinerary.copy()
    left_fares = df.copy()
    variations = []

    while left_fares.size:
        route = routes.pop(0)
        satisfactory = [index for index, fare in left_fares.iterrows() if route in fare['routes']]
        step_variations = []

        for index in satisfactory:
            fare = left_fares.loc[index]
            if not variations:
                step_variations.append(
                    {
                        'price': fare['price'],
                        'routes': fare['routes'],
                        'fares': [index]
                    }
                )
            else:
                for variation in variations:
                    if route not in variation['routes']:
                        variation['price'] += fare['price']
                        variation['routes'] += fare['routes']
                        variation['fares'].append(index)

            left_fares.drop(index, inplace=True)

        if step_variations:
            variations = step_variations

    return variations


def main():
    with open(os.environ["DATA_FILE"], "r") as f:
        data = json.loads(f.read())

    answer = find_optimal_combination(data)

    with open(os.environ["RESULT_FILE"], 'w') as f:
        f.write(json.dumps(answer))


if __name__ == "__main__":
    main()
