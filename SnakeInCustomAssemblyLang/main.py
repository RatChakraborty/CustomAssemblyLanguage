import tkinter as tk
import time
import random

root = None
canvas = None
img = None
img_scaled = None
last_key = 2 #initial direction i'm starting is right

PALETTE = {
    0: "#000000", 1: "#FFFFFF", 2: "#FF0000", 
    3: "#00FF00", 4: "#0000FF", 5: "#FFB700"
}

def onKeyPress(event):
    global last_key
    key = event.keysym.lower()
    if key in ['w', 'up']: 
        last_key = 1
    elif key in ['d', 'right']: 
        last_key = 2
    elif key in ['s', 'down']: 
        last_key = 3
    elif key in ['a', 'left']: 
        last_key = 4

def initDisplay():
    global root, canvas, img, canvas_img_id
    root = tk.Tk()
    root.title("Display Screen")
    canvas = tk.Canvas(root, width=640, height=400, bg="black")
    canvas.pack()
    img = tk.PhotoImage(width=320, height=200)
    canvas_img_id = None
    root.bind("<Key>", onKeyPress)

def renderScreen(screen):
    global root, canvas, img, img_scaled, canvas_img_id
    window_alive = False
    if root is not None:
        try:
            window_alive = root.winfo_exists()
        except tk.TclError:
            window_alive = False

    if not window_alive:
        initDisplay()
        
    img_data = []
    for y in range(200):
        row = [PALETTE.get(screen[y][x], "#FFFFFF") for x in range(320)]
        img_data.append("{" + " ".join(row) + "}")
        
    img.put(" ".join(img_data))
    img_scaled = img.zoom(2, 2)
    
    if canvas_img_id is None:
        canvas_img_id = canvas.create_image(0, 0, image=img_scaled, anchor="nw")
    else:
        try:
            canvas.itemconfig(canvas_img_id, image=img_scaled)
        except tk.TclError:
            initDisplay()
            canvas_img_id = canvas.create_image(0, 0, image=img_scaled, anchor="nw")
        
    try:
        root.update_idletasks()
        root.update()
    except tk.TclError:
        pass

def listMaker(program):
    return [line.strip() for line in program.splitlines()]

def commentRemover(program):
    return [line for line in listMaker(program) if line != "" and line[0] != "!"]

def getLocalVar(localVars, varName):
    index = int(varName[1:])
    if index >= len(localVars):
        return 0
    else:
        return localVars[index]

def setLocalVar(localVars, varName, value):
    index = int(varName[1:])
    if index >= len(localVars):
        while len(localVars) <= index:
            localVars.append(0)
    localVars[index] = value
 
def evaluateSingular(operand, args, localVars):
    if operand.startswith("A"):
        index = int(operand[1:])
        return args[index]
    elif operand.startswith("L"):
        return getLocalVar(localVars, operand)
    else:
        return int(operand)
        
def expressionEvaluator(expressionParts, args, localVars):
    if len(expressionParts) == 1:
        return evaluateSingular(expressionParts[0], args, localVars)
    else:
        operator = expressionParts[0]
        operand1 = evaluateSingular(expressionParts[1], args, localVars)
        operand2 = evaluateSingular(expressionParts[2], args, localVars)
    
        if operator == "+":
            return operand1 + operand2
        elif operator == "-":
            return operand1 - operand2
    
def jumper(myProgram, line, args, localVars):
    myLine = line.split()
    
    if myLine[0] == "JMP":
        location = myLine[1] 
        location += ":"
        return myProgram.index(location)
        
    elif myLine[0] == "JMP0":
        value = evaluateSingular(myLine[1], args, localVars)
        if value == 0:
            location = myLine[2] 
            location += ":"
            return myProgram.index(location)
        return None

    elif myLine[0] == "JMP+":
        value = evaluateSingular(myLine[1], args, localVars)
        if value > 0:
            location = myLine[2]
            location += ":"
            return myProgram.index(location)
        return None

def returner(line, args, localVars):
    listLine = [char for char in line.split()]
    return evaluateSingular(listLine[1], args, localVars)

def executor(program, args):
    myProgram = commentRemover(program)
    lineNumber = 0
    localVariables = []
    screen = [[0 for _ in range(320)] for _ in range(200)]
    
    while lineNumber < len(myProgram):
        currentLine = myProgram[lineNumber]
        toProcess = currentLine.split()
        
        if toProcess[0].endswith(':'):
            lineNumber += 1
        elif toProcess[0][0] == 'L':
            value = expressionEvaluator(toProcess[1:], args, localVariables)
            setLocalVar(localVariables, toProcess[0], value)
            lineNumber += 1
        elif toProcess[0] == 'RTN':
            return returner(currentLine, args, localVariables)
        elif toProcess[0] == 'JMP' or toProcess[0] == 'JMP+' or toProcess[0] == 'JMP0':
            newLine = jumper(myProgram, currentLine, args, localVariables)
            if newLine == None:
                lineNumber += 1
            else:
                lineNumber = newLine

        elif toProcess[0] == 'PIX':
            x = evaluateSingular(toProcess[1], args, localVariables)
            y = evaluateSingular(toProcess[2], args, localVariables)
            c = evaluateSingular(toProcess[3], args, localVariables)
            if 0 <= x < 320 and 0 <= y < 200:
                screen[y][x] = c
            lineNumber += 1
    
        elif toProcess[0] == 'RENDER':
            renderScreen(screen)
            lineNumber += 1

        elif toProcess[0] == 'KEY':
            setLocalVar(localVariables, toProcess[1], last_key)
            lineNumber += 1

        elif toProcess[0] == 'WAIT':
            ms = evaluateSingular(toProcess[1], args, localVariables)
            time.sleep(ms / 1000.0)
            lineNumber += 1

        elif toProcess[0] == 'RAND':
            max_val = evaluateSingular(toProcess[2], args, localVariables)
            setLocalVar(localVariables, toProcess[1], random.randint(0, max_val - 1))
            lineNumber += 1

        elif toProcess[0] == 'GET':
            idx = evaluateSingular(toProcess[2], args, localVariables)
            val = getLocalVar(localVariables, f"L{idx}")
            setLocalVar(localVariables, toProcess[1], val)
            lineNumber += 1

        elif toProcess[0] == 'SET':
            idx = evaluateSingular(toProcess[1], args, localVariables)
            val = evaluateSingular(toProcess[2], args, localVariables)
            setLocalVar(localVariables, f"L{idx}", val)
            lineNumber += 1

if __name__ == "__main__":
    with open("snake.txt", "r") as f:
        snake_program = f.read()
    
    executor(snake_program, [])
        








