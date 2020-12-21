import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.dates as dates
import matplotlib.ticker as ticker
import pickle
import pyttsx3
# from playsound import playsound


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


def parse_parameters(url, func, parameters_count, starting_string, end_string):
    parameters_array = []
    for i in range(parameters_count):
        parameters_array.append([])

    response = requests.get(url, timeout=10000)
    saved_response_file = open((url+'_saved').replace('/', '').replace(':', ''), 'wb')
    pickle.dump(response, saved_response_file)
    text = response.text.replace('null', '0')
    begin = text.find(starting_string) + len(starting_string)
    end = text.find(end_string)
    ret_data = func(text[begin:end])

    for i in range(parameters_count):
        parameters_array[i].append(ret_data[i])

    while 'arg' in ret_data[0]:
        ret_data = func(ret_data[0])
        for i in range(parameters_count):
            parameters_array[i].append(ret_data[i])

    return tuple(map(tuple, parameters_array))


def draw_plot(x_vals, y_vals, x_axis_label, y_axis_label, label):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)

    ax.scatter(x_vals, y_vals, color='blue', s=4, label='Surowe dane')
    ax.plot(x_vals, moving_average(7, y_vals), color='red', alpha=1, label='Średnia z 5 dni')
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
    datemin = np.datetime64(x_vals[0], 'D')
    datemax = np.datetime64(x_vals[-1], 'D') + np.timedelta64(3, 'D')
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


engine = pyttsx3.init()
engine.setProperty('age', 70)

skip, datas_tests, ratios, ratios_tested_people, tests_array, new_cases \
    = parse_parameters("https://koronawirusunas.pl/u/polska-testy-nowe", get_tests_values, 6, 'var Data_przyrost_testy = [', 'var TstartData = ')
skip, datas_deaths, dr_ratios, deaths_daily \
    = parse_parameters("https://koronawirusunas.pl/u/polska-nowe", get_deaths_recovered_values, 4, 'var populationData = [', 'var startData = ')


draw_plot(datas_tests, ratios, 'Data', 'Udział wyników pozytywnych [%]', 'Stosunek testów pozytywnych do wszystkich testów')
draw_plot(datas_tests, tests_array, 'Data', 'Liczba testów', 'Liczba dziennie wykonanych testów')
draw_plot(datas_tests, new_cases, 'Data', 'Liczba zakażeń', 'Liczba dziennie wykrytych zakażeń')
draw_plot(datas_deaths, dr_ratios, 'Data', 'Liczba zmarłych / liczba wyleczonych', 'Stosunek liczby zmarłych do wyleczonych - dziennie')
draw_plot(datas_deaths, deaths_daily, 'Data', 'Liczba zgonów', 'Liczba zgonów - dziennie')

print('_________________________________')

print('Dane z', datas_tests[-1])
print('Liczba testów:', tests_array[-1])
print('Liczba zakażeń:', new_cases[-1])
print('Liczba zgonów:', deaths_daily[-1])
print('Stosunek wyników pozytywnych:', ratios[-1])
print('Stosunek zgonów do wyzdrowień:', dr_ratios[-1])
engine.say('Dane z' + str(datas_tests[-1]))
engine.say("Liczba testów" + str(tests_array[-1]))
engine.say("Liczba zakażeń" + str(new_cases[-1]))
engine.say("Liczba zgonów" + str(deaths_daily[-1]))
engine.say("Stosunek wyników pozytywnych:" + str(round(ratios[-1], 1)) + 'procent')
engine.say("Stosunek zgonów do wyzdrowień:" + str(round(dr_ratios[-1], 1)) + 'procent')
plt.ion()
plt.pause(0.001)
plt.show()
engine.runAndWait()
