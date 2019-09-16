from operator import itemgetter

# 1. 파일을 읽어 주문 리스트 만들기
# 1.1. 모드와 기계 수, 파일 숫자를 설정
mode = 'hard'
num_machine = 20
file_num = 9

# 1.2 mode와 기계 수를 이용하여 기계 최대 생산 능력 설정
if mode == "easy":
    if num_machine == 16:
        make_span = 15
    elif num_machine == 20:
        make_span = 24
elif mode == "normal":
    if num_machine == 16:
        make_span = 14
    elif num_machine == 20:
        make_span = 22
elif mode == "hard":
    if num_machine == 16:
        make_span = 13
    elif num_machine == 20:
        make_span = 20

# 1.3 1번을 이용하여 주문 리스트 파일을 읽어 order_list로 저장
folder = str(num_machine)+mode
file_name = 'orderlist' + str(num_machine)+'_' + str(file_num)
f = open(folder+'/'+file_name+'.txt', 'r')
order_list = list()
info_order_list = f.readline()[:-1].split(',')
num_product = int(info_order_list[1])  # 파일의 첫 줄에 적혀있는 제품 수를 num_product로 저장

while True:
    line = f.readline()
    if not line:
        break
    order = line[:-1].split(',')
    product = order[0]
    order_amt = int(order[1])
    due_date = int(order[2])
    order_list.append([product, order_amt, due_date])
f.close()

num_order = len(order_list)  # 총 주문 개수를 num_order로 저장
"---------------------------------------------------------------------------------------------------------------------"

# 2. slack -> EDD 순으로 정렬
# 2.1 order_amt와 due date를 이용하여 slack을 만들어 order_list에 추가
for i in range(num_order):
    order_amt = order_list[i][1]
    prod_time = int(order_amt/10)
    due_date = order_list[i][2]
    slack = due_date - prod_time
    order_list[i].append(slack)

# 2.2 slack 기준 정렬
order_list.sort(key=itemgetter(3))
slack_list = list()

# 2.3 slack이 같은 주문들을 임시 리스트에 저장 후 EDD 순으로 정렬
for i in range(num_order):
    slack = order_list[i][3]
    slack_list.append(slack)

slack_set = set(slack_list)  # set을 이용하여 중복 제거
slack_count = {}  # slack 별 주문 갯수
sorted_order_list = list()
order_index = 0

for i in slack_set:
    temp_list = list()

    while order_index < num_order:
        slack = order_list[order_index][3]
        if slack == i:
            temp_list.append(order_list[order_index])
            order_index += 1
        else:
            break

        slack_count[i] = len(temp_list)
        temp_list.sort(key=itemgetter(2))

    for j in temp_list:
        sorted_order_list.append(j)


order_list = sorted_order_list

"""------------------------------------------------------------------------------------------------------------------"""
# 3. 조건(작업 변경 X, 납기일 초과 X)을 만족하는 제품을 기계에 배치

over_date = 0  # 납기일 초과 횟수
job_change = 0  # 작업 변경 횟수
number = 0  # 배치 순서

machine = list()
# 3.1 기계 대수만큼 제품을 배치
for i in range(num_machine):
    # 3.2 각 기계의 첫번째 생산은 slack이 제일 작으면서 납기일이 제일 빠른 제품을 생산
    machine.append(list())
    machine_capacity = make_span
    product = order_list[0][0]
    order_amt = order_list[0][1]
    slack = order_list[0][3]
    prod_time = int(order_amt / 10)
    number += 1

    if number < 10:
        product_number = product + ' ' + str(number)
    else:
        product_number = product + str(number)

    for j in range(prod_time):
        machine[i].append(product_number)

    print("%s번 배치: %s" % (number, order_list[0]))
    order_list.pop(0)
    slack_count[slack] -= 1
    num_order = len(order_list)
    machine_capacity -= prod_time
    production_end = prod_time  # 생산 종료 시점


# 3.3 제품 생산이 끝나고 기계가 생산을 할 수 있으면 작업 변경이 없으면서 납기일까지 생산이 가능한 제품 배치
#     기계가 생산을 할 수 없으면 3.2로

    if machine_capacity != 0:
        start_point = 0  # 생산 가능 시점

# 3.4 납기일을 초과하지 않고 배치가 가능한 제품 후보 찾기 start_point 이상의 제품부터 생산이 가능
        for j in slack_set:
            if j >= production_end:
                break
            unallocated_prod = slack_count[j]
            start_point += unallocated_prod

# 3.5 이전에 생산한 제품와 같은 제품 찾아 배치
#     같은 제품이 없으면 3.2로

        while start_point < num_order:
            pre_prod = (machine[i][-1])[0]
            product = order_list[start_point][0]
            order_amt = order_list[start_point][1]
            prod_time = int(order_amt / 10)
            due_date = order_list[start_point][2]
            slack = order_list[start_point][3]
            production_end = len(machine[i]) + prod_time

            if product == pre_prod and production_end <= due_date:
                number += 1
                if number < 10:
                    product_number = product + ' ' + str(number)
                else:
                    product_number = product + str(number)

                for j in range(prod_time):
                    machine[i].append(product_number)
                print("%s번 배치: %s" % (number, order_list[start_point]))
                order_list.pop(start_point)
                num_order = len(order_list)
                slack_count[slack] -= 1
                machine_capacity -= prod_time
            else:
                start_point += 1
                continue

# 4. 작업을 변경 시켜 작업을 배치
over_date_prod = list()  # 납기일 내에 생산이 불가한 제품 목록

while num_order != 0:
    # 4.1 기계들 중 생산 능력이 가장 큰 기계 찾기
    max_machine = 0
    max_capa = make_span - len(machine[max_machine])
    for i in range(1, num_machine):
        capa = make_span - len(machine[i])
        if capa > max_capa:
            max_machine = i
            max_capa = capa

    machine_capacity = make_span - len(machine[max_machine])
    pre_prod = machine[max_machine][-1]
    product = order_list[0][0]
    number += 1
    order_amt = order_list[0][1]
    prod_time = int(order_list[0][1] / 10)
    due_date = order_list[0][2]
    slack = order_list[0][3]
    over_date_check = prod_time + len(machine[max_machine])

    # 4.2 제품 배치 시 납기일을 초과하면 납기일을 초과하는 제품 목록에 저장 후 4.1로
    if over_date_check > due_date:
        over_date_prod .append(order_list.pop(0))
        num_order = len(order_list)
        number -= 1
        continue

    # 4.3 납기일 내에 생산이 가능하면 slack이 가장 작고 납기일이 가장 빠른 제품을 배치 후 job_change + 1

    if number < 10:
        product_number = product + ' ' + str(number)
    else:
        product_number = product + str(number)
    print("작업 변경 %s -> %s" % (pre_prod, product_number))
    for i in range(prod_time):
        machine[max_machine].append(product_number)

    print("%s번 배치: %s" % (number, order_list[0]))
    order_list.pop(0)
    slack_count[slack] -= 1
    num_order = len(order_list)
    machine_capacity -= prod_time
    production_end = len(machine[max_machine])
    job_change += 1

    # 4.5 3.3 ~ 3.5와 동일
    if machine_capacity > 0:
        start_point = 0
        for i in slack_set:
            if i >= prod_time:
                break
            unallocated_prod = slack_count[i]
            start_point += unallocated_prod

            while start_point < num_order:
                pre_prod = (machine[max_machine][-1])[0]
                product = order_list[start_point][0]
                order_amt = order_list[start_point][1]
                prod_time = int(order_amt / 10)
                due_date = order_list[start_point][2]
                slack = order_list[start_point][3]
                production_end = len(machine[max_machine]) + prod_time

                if product == pre_prod and production_end <= due_date:
                    number += 1
                    if number < 10:
                        product_number = product + ' ' + str(number)
                    else:
                        product_number = product + str(number)

                    for j in range(prod_time):
                        machine[max_machine].append(product_number)
                    print("%s번 배치: %s" % (number, order_list[start_point]))
                    order_list.pop(start_point)
                    num_order = len(order_list)
                    slack_count[slack] -= 1
                    machine_capacity -= prod_time
                else:
                    start_point += 1
                    continue

# 5. 납기일을 초과하는 제품 배치
num_over_date = len(over_date_prod)  # 납기일을 초과하는 제품 수
violated_prod = list()  # 납기일을 초과하는 제품 리스트

while num_over_date != 0:
    number += 1
    product = over_date_prod[0][0]
    order_amt = over_date_prod[0][1]
    due_date = over_date_prod[0][2]
    slack = over_date_prod[0][3]
    prod_time = int(over_date_prod[0][1] / 10)

    # 5.1 마지막으로 생산한 제품이 배치할 제품과 같은 기계 중 생산 능력이 가장 큰 기계 찾기
    # 마지막으로 생산한 제품이 배치할 제품과 같은 기계가 없을 경우 생산 능력이 가장 큰 기계에 배치
    machine_list = list()
    for i in range(num_machine):

        if product == (machine[i][-1])[0]:
            machine_list.append(i)

    if len(machine_list) != 0:
        max_machine = machine_list[0]
        max_capa = len(machine[max_machine])
        for i in machine_list:
            capa = len(machine[i])
            if capa < max_capa:
                max_machine = i
                max_capa = capa
    else:
        job_change += 1
        max_machine = 0
        max_capa = make_span - len(machine[max_machine])

        for i in range(1, num_machine):
            capa = make_span - len(machine[i])
            if capa > max_capa:
                max_machine = i
                max_capa = capa
        max_machine = i
        max_capa = len(machine[max_machine])
        pre_prod = machine[max_machine][-1]

        if number < 10:
            product_number = product + ' ' + str(number)
        else:
            product_number = product + str(number)
        print("작업 변경 %s -> %s" % (pre_prod, product_number))

    # 5.2 slack이 가장 작고 due date가 가장 빠른 제품 배치
    if number < 10:
        product_number = product + ' ' + str(number)
    else:
        product_number = product + str(number)
    violated_prod.append(product_number)
    for j in range(prod_time):
        machine[max_machine].append(product_number)

    over = len(machine[max_machine]) - due_date
    print("납기일 초과: %s (%s일 초과)" %(product_number, over))
    print("%s번 배치: %s" % (number, over_date_prod[0]))
    over_date_prod.pop(0)
    num_over_date = len(over_date_prod)
    slack_count[slack] -= 1
    machine_capacity -= prod_time
    over_date += 1

# 배치 결과를 차트로 만들고 비용 계산
cost = over_date * 10 + job_change * 2
gant_chart_txt = open(folder+'_chart/'+file_name+'.txt', 'w')
print('')
print(file_name + ' 간트 차트')
print('')
print('    ', end='')
gant_chart_txt.write('    ')
for i in range(make_span):
    if i < 10:
        print(' ', end='')
        gant_chart_txt.write(' ')
    print(str(i+1)+'      ', end='')

    gant_chart_txt.write(str(i+1)+'      ')
print('')
gant_chart_txt.write('\n')
print('   ', end='')
gant_chart_txt.write('   ')
print('--------'*make_span)
gant_chart_txt.write('--------'*make_span)
gant_chart_txt.write('\n')
for i in range(num_machine):
    if i < 9:
        print(' ', end='')
        gant_chart_txt.write(' ')
    print(str(i+1)+'|  ', end='')
    gant_chart_txt.write(str(i+1)+'|  ')
    for j in machine[i]:
        if j[1:] == '100':
            print(j + '    ', end='')
            gant_chart_txt.write(j + '    ')
        else:
            print(j+'     ', end='')
            gant_chart_txt.write(j+'     ')
    print('')
    gant_chart_txt.write('\n')

print('   ', end='')
gant_chart_txt.write('   ')
print('--------'*make_span)
gant_chart_txt.write('--------'*make_span+'\n')
print('')
gant_chart_txt.write('\n')
print('job change: '+str(job_change))
gant_chart_txt.write('job change: '+str(job_change)+'\n')
print('violated product: ', end='')
gant_chart_txt.write('violated product: ')
for i in violated_prod:
    print(i + ', ', end='')
    gant_chart_txt.write(i+', ')
print('')
gant_chart_txt.write('\n')
print('due date violation: '+str(over_date))
gant_chart_txt.write('due date violation: '+str(over_date)+'\n')
print('cost: '+str(cost))
gant_chart_txt.write('cost: '+str(cost)+'\n')
