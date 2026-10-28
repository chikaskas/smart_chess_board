
# Made partially by Google's Gemini AI

import machine as m
import sys
import select
import time
import coms

jdy_uart = m.UART(0, baudrate=115200, tx=m.Pin(0), rx=m.Pin(1))
#sys.stdin.read(1) returns string of lenght 1
#use send(f'R: {str(bytes(usb_data, 'utf-8'))} \n')
led = m.Pin(23, m.Pin.OUT)

# Set up a poll object to monitor incoming USB data without blocking
poll_object = select.poll()
poll_object.register(sys.stdin, select.POLLIN)

scan_time = 42.96#ms

led_duty = 500#ms
started_sending = 0
scans_sent = 0
current_board = [
    ['r','n','b','q','k','b','n','r'],
    ['p','p','p','p','p','p','p','p'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['P','P','P','P','P','P','P','P'],
    ['R','N','B','Q','K','B','N','R']
]

def send(message):
    # Send the data
    jdy_uart.write(message)
    
    # Wait for the duration of the whole transmission
    time.sleep(len(message) * 0.001)

while True:
    current_time = time.ticks_ms()

    if poll_object.poll(0):
        usb_data = sys.stdin.read(1)

        if usb_data == 'V':
            usb_data += sys.stdin.read(2)
            if coms.check_block_crc(usb_data):
                sys.stdout.write('v01287D')
                send(f'R: {usb_data} CRC matched \n')
                send(f'S: {'v01287D'} \n')
            else:
                send(f'R: {usb_data} CRC failed\n')

        elif usb_data == 'W':
            usb_data += sys.stdin.read(6)
            if coms.check_block_crc(usb_data):
                send(f'R: {usb_data} CRC matched\n')
                to_send = coms.add_block_crc(f'w{usb_data[1:5]}')
                sys.stdout.write(to_send)
                send(f'S: {to_send} \n')
                if usb_data[1:5] == '0200':
                    started_sending = current_time
            else:
                send(f'R: {usb_data} CRC failed\n')
        
        elif usb_data == 'X':
            usb_data += sys.stdin.read(2)
            if coms.check_block_crc(usb_data):
                sys.stdout.write('x78')
                send(f'R: {usb_data} CRC matched \n')
                send(f'S: {'x78'} \n')
            else:
                send(f'R: {usb_data} CRC failed\n')
        
        elif usb_data == 'L':
            usb_data += sys.stdin.read(166)
            if coms.check_block_crc(usb_data):
                sys.stdout.write('l6C')
                #send(f'R: {usb_data[:5]}...{usb_data[-4:]} CRC matched \n')
                send(f'R: {usb_data} CRC matched \n')
                send(f'S: {'l6C'} \n')
                send('Updated board:\n')
                board = ''
                clean = usb_data[3:-2]
                for x in range(9):
                    for y in range(9):
                        send(f' {clean[2*(y*9+x):2*(y*9+x)+2]}  ')
                    send('\n\n')
            else:
                send(f'R: {usb_data} CRC failed\n')

        else:
            send(f'New command: {usb_data} \n')
    

    if jdy_uart.any():
        data = jdy_uart.read().decode("utf-8")
        if data[:5] != 'ERROR':
            numbers = ['8', '7', '6', '5', '4', '3', '2', '1']
            letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            if (data[0] in letters) and (data[1] in numbers) and (data[2] in letters) and (data[3] in numbers):
                current_board[numbers.index(data[3])][letters.index(data[2])] = current_board[['8', '7', '6', '5', '4', '3', '2', '1'].index(data[1])][['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'].index(data[0])]
                current_board[numbers.index(data[1])][letters.index(data[0])] = '.'
                send('Updated board to:\n')
                for row in current_board:
                    send(str(row)+'\n')
            else:
                send('Invalid move')

    if ((current_time - started_sending)/scan_time > scans_sent) and (started_sending != 0):
        board = 's'
        for row in current_board:
            for piece in row:
                board += piece
        sys.stdout.write(coms.add_block_crc(board))
        scans_sent += 1
    
    if (current_time % led_duty) > led_duty // 2:
        led.on()
    else:
        led.off()
