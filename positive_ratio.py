import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.dates as dates
import matplotlib.ticker as ticker


def get_tests_values(text):
    first_val = text[text.find('arg: "') + len('arg: "'): text.find('},')]
    data_dots = first_val[0: first_val.find('"')]
    data_arr = data_dots.split('.')
    data = data_arr[2] + '-' + data_arr[1] + '-' + data_arr[0]

    tests_amount = int(first_val[first_val.find('p_testy: ') + len('p_testy: '): first_val.find('p_testyl') - 1])
    tested_people = int(first_val[first_val.find('p_testyl: ') + len('p_testyl: '): first_val.find('p_chorzy') - 1])
    positive_results = int(first_val[first_val.find('p_chorzy: ') + len('p_chorzy: '): first_val.find('},')])

    if tests_amount != 0:
        positive_tests_ratio = 100 * float(positive_results) / float(tests_amount)
    else:
        positive_tests_ratio = 0

    if tested_people != 0:
        positive_ratio_tested_people = 100 * positive_results / tested_people
    else:
        positive_ratio_tested_people = 0
    print(data, tests_amount, positive_results, positive_tests_ratio, positive_ratio_tested_people)

    return text[text.find('},') + len('},'):], np.datetime64(data,
                                                             'D'), positive_tests_ratio, positive_ratio_tested_people, tests_amount, positive_results


def get_deaths_recovered_values(text):
    first_val = text[text.find('arg: "') + len('arg: "'): text.find('},')]
    data = first_val[0: first_val.find('"')]
    sick = int(first_val[first_val.find('p_chorzy: ') + len('p_chorzy: '): first_val.find('p_zgony') - 1])
    deaths = int(first_val[first_val.find('p_zgony: ') + len('p_zgony: '): first_val.find('p_wyleczeni') - 1])
    recovered = int(first_val[first_val.find('p_wyleczeni: ') + len('p_wyleczeni: '): first_val.find('},')])
    data_arr = data.split('.')
    data = data_arr[2] + '-' + data_arr[1] + '-' + data_arr[0]

    if recovered != 0:
        death_recovered_ratio = 100 * float(deaths) / int(recovered)
    else:
        death_recovered_ratio = 0

    print(data, sick, deaths, recovered, death_recovered_ratio)

    return text[text.find('},') + len('},'):], np.datetime64(data, 'D'), death_recovered_ratio, deaths


def parse_parameters(url, func, parameters, starting_string, end_string):
    # url = "https://koronawirusunas.pl/u/polska-testy-nowe"
    response = requests.get(url, timeout=10000)
    text = response.text.replace('null', '0')
    # begin = text.find('var Data_przyrost_testy = [') + len('var Data_przyrost_testy = [')
    begin = text.find(starting_string + len(starting_string))
    # end = text.find('var TstartData = ')
    end = text.find(end_string)

    # text, d, r, r_tested_people, tests, positive = get_tests_values(text[begin:end])
    ret_data = func(text[begin:end])
    parameters_arrays = [[]] * len(parameters)
    for i in range(len(parameters)):
        parameters_arrays[i].append(ret_data[i])
    #
    # ratios = [r]
    # datas = [d]
    # tests_array = [tests]
    # new_cases = [positive]

    while 'arg' in text:
        ret_data = get_tests_values(text)
        for i in range(len(parameters)):
            parameters_arrays[i].append(ret_data[i])


def draw_plot(x_vals, y_vals, x_axis_label, y_axis_label, label):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)

    # data = [datas, ratios]
    ax.scatter(x_vals, y_vals, color='blue', s=4, label='Surowe dane')
    ax.plot(x_vals, moving_average(5, y_vals), color='red', alpha=1, label='Średnia z 5 dni')
    plt.axvline(x=np.datetime64('2020-11-04', 'D'), label='Konferencja ws lockdownu', c='black', linestyle=':')
    plt.axvline(x=np.datetime64('2020-07-01', 'D'), label='Koronawirus "w odwrocie"', c='orange', linestyle=':')
    plt.legend(bbox_to_anchor=(0., -0.4, 1., 0.), loc='lower left')

    # format the ticks
    ax.xaxis.set_major_locator(dates.MonthLocator())
    # 16 is a slight approximation since months differ in number of days.
    ax.xaxis.set_minor_locator(dates.MonthLocator(bymonthday=16))

    ax.xaxis.set_major_formatter(ticker.NullFormatter())
    ax.xaxis.set_minor_formatter(dates.DateFormatter('%b'))

    # round to nearest years.
    datemin = np.datetime64(datas[0], 'D')
    datemax = np.datetime64(datas[-1], 'D') + np.timedelta64(3, 'D')
    ax.set_xlim(datemin, datemax)
    fig.autofmt_xdate()
    fig.suptitle(label)
    plt.subplots_adjust(None, 0.27)


def moving_average(step, arr):
    averaged = []
    for i, val in enumerate(arr):
        if (i - step) > 0:
            subarray_avg = np.mean(arr[i - step:i + 1])
        else:
            subarray_avg = np.mean(arr[0:i + 1])

        averaged.append(subarray_avg)

    return averaged


years = mdates.YearLocator()  # every year
months = mdates.MonthLocator()  # every month
months_fmt = mdates.DateFormatter('%M')

url = "https://koronawirusunas.pl/u/polska-testy-nowe"
response = requests.get(url, timeout=10000)
text = response.text.replace('null', '0')
begin = text.find('var Data_przyrost_testy = [') + len('var Data_przyrost_testy = [')
end = text.find('var TstartData = ')

text, d, r, r_tested_people, tests, positive = get_tests_values(text[begin:end])

ratios = [r]
datas = [d]
tests_array = [tests]
new_cases = [positive]

while 'arg' in text:
    text, d, r, r_tested_people, tests, positive = get_tests_values(text)
    ratios.append(r)
    datas.append(d)
    tests_array.append(tests)
    new_cases.append(positive)

url_deaths = "https://koronawirusunas.pl/u/polska-nowe"
response = requests.get(url_deaths, timeout=10000)
text = response.text.replace('null', '0')
begin = text.find('var populationData = [') + len('var populationData = [')
end = text.find('var startData = ')
text, d, deaths_recovered_ratio, deaths = get_deaths_recovered_values(text[begin:end])
dr_ratios = [deaths_recovered_ratio]
death_daily = [deaths]
datas2 = [d]

while 'arg' in text:
    text, d, deaths_recovered_ratio, deaths = get_deaths_recovered_values(text)
    dr_ratios.append(deaths_recovered_ratio)
    datas2.append(d)
    death_daily.append(deaths)

draw_plot(datas, ratios, 'Data', 'Udział wyników pozytywnych [%]', 'Stosunek testów pozytywnych do wszystkich testów')
draw_plot(datas, tests_array, 'Data', 'Liczba testów', 'Liczba dziennie wykonanych testów')
draw_plot(datas, new_cases, 'Data', 'Liczba zakażeń', 'Liczba dziennie wykrytych zakażeń')
draw_plot(datas2, dr_ratios, 'Data', 'Liczba zmarłych / liczba wyleczonych',
          'Stosunek liczby zmarłych do wyleczonych - dziennie')
draw_plot(datas2, death_daily, 'Data', 'Liczba zgonów',
          'Liczba zgonów - dziennie')
print('_________________________________')
print('Dane z', datas[-1])
print('Liczba testów:', tests_array[-1])
print('Liczba zakażeń:', new_cases[-1])
print('Liczba zgonów:', death_daily[-1])
print('Stosunek wyników pozytywnych:', ratios[-1])
print('Stosunek zgonów do wyzdrowień:', dr_ratios[-1])

plt.show()
