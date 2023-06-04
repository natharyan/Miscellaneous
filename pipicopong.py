import math
from machine import Pin, SoftI2C
import ssd1306
from picozero import Pot
from time import sleep
import random

# return the sign of x (+1 or -1)
def sgn(x):
    if x < 0:
        return -1
    else:
        return 1

# the input thing is in the range [minin, maxin], the output should be in
# the range [minout, maxout] with linear scaling
def remap(thing, minin, maxin, minout, maxout):
    val = (maxout-minout)/(maxin-minin)
    return (minout + (thing-minin)*val)

# the input thing is in any range, the output should be thing clamped (truncated)
# to the range [minout, maxout]
def clamp(thing, minout, maxout):
    if thing>maxout:
        return maxout
    elif thing<minout:
        return minout
    else:
        return thing

# assume that the I2C SDA connection for an OLED is present at pin GP(sda)
# and the SCL/SCK connection is present at the GP(sda + 1), return an SSD1306 object
def oled_connect(sda):
    i2c = SoftI2C(sda = Pin(sda), scl = Pin(sda + 1))
    return ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

def get_y_position(pot):
    return int(remap(pot.value,POTENTIO_MIN,POTENTIO_MAX,0,HEIGHT- PADDLE_DIMS[1]))



FRAME_RATE = 60
PADDLE_DIMS = (5, 25)
BALL_DIMS = (5, 5)

WIDTH = 128
HEIGHT = 64

OLED_ATTACH = 2
POT_IN = 0

POTENTIO_MIN = 0.002
POTENTIO_MAX = 0.99

oled = oled_connect(OLED_ATTACH)
pot = Pot(POT_IN)

score = (0, 0)

ball = [0,0,0,0]

# helper functions
def draw_paddles(oled,paddle):
    oled.fill_rect(paddle[0],paddle[1],PADDLE_DIMS[0],PADDLE_DIMS[1],1)
    
def reset_ball():
    yv = random.randint(-3, 3)
    while yv == 0:
        yv = random.randint(-3, 3)
    
    # The ball is placed at the center of the screen
    return ((WIDTH - BALL_DIMS[0]) // 2, (HEIGHT - BALL_DIMS[1]) // 2, 2, yv)

def draw_ball(ball):
    oled.fill_rect(ball[0],ball[1],BALL_DIMS[0],BALL_DIMS[1],1)
    
def rect_intersection(A, B, x_off = 0, y_off = 0):
    # no intersection if any of the widths or heights are 0
    if A[2] == 0 or A[3] == 0 or B[2] == 0 or B[3] == 0:
        return False
    # if A is completely to the right of B or B is completely to the right of A
    if A[0] + x_off > B[0] + B[2] or B[0] > A[0] + x_off + A[2]:
        return False
    # if A is completely below B or B is completely below A
    if A[1] + y_off > B[1] + B[3] or B[1] > A[1] + y_off + A[3]:
        return False
    return True

def update_ball(ball,paddles):
    global score
    x, y, xv, yv = ball
    # A: paddle collisions
    ball_bb = (x, y, BALL_DIMS[0], BALL_DIMS[1])
    
    for paddle in paddles:
        paddle_collision = False
        test_bb = (paddle[0], paddle[1], PADDLE_DIMS[0], PADDLE_DIMS[1])     
        if yv != 0 and rect_intersection(ball_bb, test_bb, 0, yv):
            paddle_collision = True
            while not rect_intersection(ball_bb, test_bb, 0, sgn(yv)):
                y += sgn(yv)
                ball_bb = (x, y, BALL_DIMS[0], BALL_DIMS[1])
            yv *= -1
        if not paddle_collision and xv != 0 and rect_intersection(ball_bb, test_bb, xv):
            paddle_collision = True
            while not rect_intersection(ball_bb, test_bb, sgn(xv)):
                x += sgn(xv)
                ball_bb = (x, y, BALL_DIMS[0], BALL_DIMS[1])
            xv *= -1
        
        if paddle_collision:
            return (x, y, xv, yv)

    
    # B: horizontal wall collisions
    reset = x < 0 or x >= WIDTH - BALL_DIMS[0]
    if x < 0:
        score = (score[0], score[1] + 1)
    if x >= WIDTH - BALL_DIMS[0]:
        score = (score[0] + 1, score[1])
    if reset:
        return reset_ball()
    # C: vertical wall bounces
    if y < 0:
        y = 0
        yv *= -1
        return (x, y, xv, yv)
    
    if y > HEIGHT - BALL_DIMS[1]:
        y = HEIGHT - BALL_DIMS[1]
        yv *= -1
        return (x, y, xv, yv)
    # D: no collisions
    return (round(x + xv), round(y + yv), xv, yv)

ball = reset_ball()

# this is our game loop
while True:
    oled.fill(0)
    pos = get_y_position(pot)
    paddle_l = (0, pos)
    paddle_r = (128-PADDLE_DIMS[0], ball[1])
    
    draw_paddles(oled,paddle_l)
    draw_paddles(oled,paddle_r)
    ball = update_ball(ball, [paddle_l, paddle_r])
    draw_ball(ball)

    oled.show()
    sleep(1 / FRAME_RATE)
    

