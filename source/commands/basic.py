#! /usr/bin/python

# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""This class implements a BASIC interpreter that
presents a prompt to the user. The user may input
program statements, list them and run the program.
The program may also be saved to disk and loaded
again.

"""

#from basictoken import BASICToken as Token
#from lexer import Lexer
#from program import Program
from sys import stderr
import math
import random
try:
    from time import ticks_ms as monotonic
except:
    from time import monotonic


class FlowSignal:

    # Jump categories

    # Indicates a simple jump as the result
    # of a GOTO or conditional branch. The
    # ftarget value should be the jump target, i.e.
    # the line number being jumped to
    SIMPLE_JUMP        = 0

    # Indicates a subroutine call where the
    # return address must be the line number of the instruction
    # of the following the call.
    # The ftarget value should be the line number of the first line
    # of the subroutine
    GOSUB              = 1

    # Indicates the start of a FOR loop where loop
    # variable has not reached the end value, and therefore the loop
    # must be repeated. There should be therefore be
    # no ftarget value associated with it
    LOOP_BEGIN         = 2

    # An indication from a processed NEXT statement that the loop is to
    # be repeated. Since the return address is already on the stack,
    # there does not need to be an ftarget value associated with the signal.
    LOOP_REPEAT        = 3

    # An indication from a FOR statement that the loop should be skipped because
    # loop variable has reached its end value. The ftarget should be
    # the loop variable to look for in the terminating NEXT statement
    LOOP_SKIP          = 4

    # Indicates a subroutine return has been processed, where the return
    # address is on the return stack. There should be therefore
    # be no ftarget value specified
    RETURN             = 5

    # Indicates that execution should cease because a stop statement has
    # been processed. There should be therefore be no ftarget value specified
    STOP               = 6

    # Indicates that a conditional result block should be executed
    EXECUTE            = 7

    def __init__(self, ftarget=None, ftype=SIMPLE_JUMP, floop_var=None):
        """Creates a new FlowSignal for a branch. If the jump
        target is supplied, then the branch is assumed to be
        either a GOTO or conditional branch and the type is assigned as
        SIMPLE_JUMP. If no jump_target is supplied, then a jump_type must be
        supplied, which must either be GOSUB, RETURN, LOOP_BEGIN,
        LOOP_REPEAT, LOOP_SKIP or STOP. In the latter cases
        the jump target is assigned an arbitrary value of None.

        :param ftarget: The associated value
        :param ftype: Either GOSUB, SIMPLE_JUMP, RETURN, LOOP_BEGIN,
        LOOP_SKIP or STOP
        :param floop_var: The loop variable of a FOR/NEXT loop
        """

        if ftype not in [self.GOSUB, self.SIMPLE_JUMP, self.LOOP_BEGIN,
                         self.LOOP_REPEAT, self.RETURN,
                         self.LOOP_SKIP, self.STOP, self.EXECUTE]:
            raise TypeError("Invalid flow signal type supplied: " + str(ftype))

        if ftarget == None and \
           ftype in [self.SIMPLE_JUMP, self.GOSUB, self.LOOP_SKIP]:
            raise TypeError("Invalid jump target supplied for flow signal type: " + str(ftarget))

        if ftarget != None and \
           ftype in [self.RETURN, self.LOOP_BEGIN, self.LOOP_REPEAT,
                     self.STOP, self.EXECUTE]:
            raise TypeError("Target wrongly supplied for flow signal " + str(ftype))

        self.ftype = ftype
        self.ftarget = ftarget
        self.floop_var = floop_var
class BASICArray:

    def __init__(self, dimensions, elem_type):
        """Initialises the object with the specified
        number of dimensions. Maximum number of
        dimensions is three

        :param dimensions: List of array dimensions and their
        corresponding sizes
        :param elem_type: Indicates whether the elements are strings ('str')
        or numbers ('num')

        """
        self.dims = min(3, len(dimensions))

        if self.dims == 0:
            raise SyntaxError("Zero dimensional array specified")

        # Check for invalid sizes and ensure int
        for i in range(self.dims):
            if dimensions[i] < 0:
                raise SyntaxError("Negative array size specified")
            # Allow sizes like 1.0f, but not 1.1f
            if int(dimensions[i]) != dimensions[i]:
                raise SyntaxError("Fractional array size specified")
            dimensions[i] = int(dimensions[i])

        # MSBASIC: Initialize to Zero
        # MSBASIC: Overdim by one, as some dialects are 1 based and expect
        #          to use the last item at index = size
        if self.dims == 1:
            if elem_type == 'num':
                self.data = [0 for x in range(dimensions[0] + 1)]
            else:
                self.data = ['' for x in range(dimensions[0] + 1)]
        elif self.dims == 2:
            if elem_type == 'num':
                self.data = [
                     [0 for x in range(dimensions[1] + 1)] for x in range(dimensions[0] + 1)
                ]
            else:
                self.data = [
                    ['' for x in range(dimensions[1] + 1)] for x in range(dimensions[0] + 1)
                ]
        else:
            if elem_type == 'num':
                self.data = [
                    [
                        [0 for x in range(dimensions[2] + 1)]
                        for x in range(dimensions[1] + 1)
                    ]
                    for x in range(dimensions[0] + 1)
                ]
            else:
                self.data = [
                    [
                        ['' for x in range(dimensions[2] + 1)]
                        for x in range(dimensions[1] + 1)
                    ]
                    for x in range(dimensions[0] + 1)
                ]

    def pretty_print(self):
        print(str(self.data))


class BASICParser:

    def __init__(self, basicdata):
        # Symbol table to hold variable names mapped
        # to values
        self.__symbol_table = {}

        # Stack on which to store operands
        # when evaluating expressions
        self.__operand_stack = []

        # BasicDATA structure containing program DATA Statements
        self.__data = basicdata
        # List to hold values read from DATA statements
        self.__data_values = []

        # These values will be
        # initialised on a per
        # statement basis
        self.__tokenlist = []
        self.__tokenindex = None

        # Previous flowsignal used to determine initializion of
        # loop variable
        self.last_flowsignal = None

        # Set to keep track of print column across multiple print statements
        self.__prnt_column = 0

        #file handle list
        self.__file_handles = {}

    def parse(self, tokenlist, line_number):
        """Must be initialised with the list of
        BTokens to be processed. These tokens
        represent a BASIC statement without
        its corresponding line number.

        :param tokenlist: The tokenized program statement
        :param line_number: The line number of the statement

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """

        # Remember the line number to aid error reporting
        self.__line_number = line_number
        self.__tokenlist = []
        self.__tokenindex = 0
        linetokenindex = 0
        for token in tokenlist:
            # If statements will always be the last statement processed on a line so
            # any colons found after an IF are part of the condition execution statements
            # and will be processed in the recursive call to parse
            if token.category == token.IF:
                # process IF statement to move __tokenidex to the code block
                # of the THEN or ELSE and then call PARSE recursively to process that code block
                # this will terminate the token loop by RETURNing to the calling module
                #
                # **Warning** if an IF stmt is used in the THEN code block or multiple IF statement are used
                # in a THEN or ELSE block the block grouping is ambiguous and logical processing may not
                # function as expected. There is no ambiguity when single IF statements are placed within ELSE blocks
                linetokenindex += self.__tokenindex
                self.__tokenindex = 0
                self.__tokenlist = tokenlist[linetokenindex:]

                # Assign the first token
                self.__token = self.__tokenlist[0]
                flow = self.__stmt() # process IF statement
                if flow and (flow.ftype == FlowSignal.EXECUTE):
                    # recursive call to process THEN/ELSE block
                    try:
                        return self.parse(tokenlist[linetokenindex+self.__tokenindex:],line_number)
                    except RuntimeError as err:
                        raise RuntimeError(str(err)+' in line ' + str(self.__line_number))
                else:
                    # branch on original syntax 'IF cond THEN lineno [ELSE lineno]'
                    # in this syntax the then or else code block is not a legal basic statement
                    # so recursive processing can't be used
                    return flow
            elif token.category == token.COLON:
                # Found a COLON, process tokens found to this point
                linetokenindex += self.__tokenindex
                self.__tokenindex = 0

                # Assign the first token
                self.__token = self.__tokenlist[self.__tokenindex]

                flow = self.__stmt()
                if flow:
                    return flow

                linetokenindex += 1
                self.__tokenlist = []
            elif token.category == token.ELSE and self.__tokenlist[0].category != token.OPEN:
                # if we find an ELSE and we are not processing an OPEN statement, we must
                # be in a recursive call and be processing a THEN block
                # since we're processing the THEN block we are done if we hit an ELSE
                break
            else:
                self.__tokenlist.append(token)

        # reached end of statement, process tokens collected since last COLON (or from start if no COLONs)
        linetokenindex += self.__tokenindex
        self.__tokenindex = 0
        # Assign the first token
        self.__token = self.__tokenlist[self.__tokenindex]

        return self.__stmt()

    def __advance(self):
        """Advances to the next token

        """
        # Move to the next token
        self.__tokenindex += 1

        # Acquire the next token if there any left
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__token = self.__tokenlist[self.__tokenindex]

    def __consume(self, expected_category):
        """Consumes a token from the list

        """
        if self.__token.category == expected_category:
            self.__advance()

        else:
            raise RuntimeError('Expecting ' + Token.catnames[expected_category] +
                               ' in line ' + str(self.__line_number))

    def __stmt(self):
        """Parses a program statement

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """
        if self.__token.category in [Token.FOR, Token.IF, Token.NEXT,
                                     Token.ON]:
            return self.__compoundstmt()

        else:
            return self.__simplestmt()

    def __simplestmt(self):
        """Parses a non-compound program statement

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """
        if self.__token.category == Token.NAME:
            self.__assignmentstmt()
            return None

        elif self.__token.category == Token.PRINT:
            self.__printstmt()
            return None

        elif self.__token.category == Token.LET:
            self.__letstmt()
            return None

        elif self.__token.category == Token.GOTO:
            return self.__gotostmt()

        elif self.__token.category == Token.GOSUB:
            return self.__gosubstmt()

        elif self.__token.category == Token.RETURN:
            return self.__returnstmt()

        elif self.__token.category == Token.STOP:
            return self.__stopstmt()

        elif self.__token.category == Token.INPUT:
            self.__inputstmt()
            return None

        elif self.__token.category == Token.DIM:
            self.__dimstmt()
            return None

        elif self.__token.category == Token.RANDOMIZE:
            self.__randomizestmt()
            return None

        elif self.__token.category == Token.DATA:
            self.__datastmt()
            return None

        elif self.__token.category == Token.READ:
            self.__readstmt()
            return None

        elif self.__token.category == Token.RESTORE:
            self.__restorestmt()
            return None

        elif self.__token.category == Token.OPEN:
            return self.__openstmt()

        elif self.__token.category == Token.CLOSE:
            self.__closestmt()
            return None

        elif self.__token.category == Token.FSEEK:
            self.__fseekstmt()
            return None

        else:
            # Ignore comments, but raise an error
            # for anything else
            if self.__token.category != Token.REM:
                raise RuntimeError('Expecting program statement in line '
                                   + str(self.__line_number))

    def __printstmt(self):
        """Parses a PRINT statement, causing
        the value that is on top of the
        operand stack to be printed on
        the screen.

        """
        self.__advance()   # Advance past PRINT token

        fileIO = False
        if self.__token.category == Token.HASH:
            fileIO = True

            # Process the # keyword
            self.__consume(Token.HASH)

            # Acquire the file number
            self.__expr()
            filenum = self.__operand_stack.pop()

            if self.__file_handles.get(filenum) == None:
                raise RuntimeError("PRINT: file #"+str(filenum)+" not opened in line " + str(self.__line_number))

            # Process the comma
            if self.__tokenindex < len(self.__tokenlist) and self.__token.category != Token.COLON:
                self.__consume(Token.COMMA)

        # Check there are items to print
        if not self.__tokenindex >= len(self.__tokenlist):
            prntTab = (self.__token.category == Token.TAB)
            self.__logexpr()

            if prntTab:
                if self.__prnt_column >= len(self.__operand_stack[-1]):
                    if fileIO:
                        self.__file_handles[filenum].write("\n")
                    else:
                        print()
                    self.__prnt_column = 0

                current_pr_column = len(self.__operand_stack[-1]) - self.__prnt_column
                self.__prnt_column = len(self.__operand_stack.pop()) - 1
                if current_pr_column > 1:
                    if fileIO:
                        self.__file_handles[filenum].write(" "*(current_pr_column-1))
                    else:
                        print(" "*(current_pr_column-1), end="")
            else:
                self.__prnt_column += len(str(self.__operand_stack[-1]))
                if fileIO:
                    self.__file_handles[filenum].write('%s' %(self.__operand_stack.pop()))
                else:
                    print(self.__operand_stack.pop(), end='')

            while self.__token.category == Token.SEMICOLON:
                if self.__tokenindex == len(self.__tokenlist) - 1:
                    # If a semicolon ends this line, don't print
                    # a newline.. a-la ms-basic
                    self.__advance()
                    return
                self.__advance()
                prntTab = (self.__token.category == Token.TAB)
                self.__logexpr()

                if prntTab:
                    if self.__prnt_column >= len(self.__operand_stack[-1]):
                        if fileIO:
                            self.__file_handles[filenum].write("\n")
                        else:
                            print()
                        self.__prnt_column = 0
                    current_pr_column = len(self.__operand_stack[-1]) - self.__prnt_column
                    if fileIO:
                        self.__file_handles[filenum].write(" "*(current_pr_column-1))
                    else:
                        print(" "*(current_pr_column-1), end="")
                    self.__prnt_column = len(self.__operand_stack.pop()) - 1
                else:
                    self.__prnt_column += len(str(self.__operand_stack[-1]))
                    if fileIO:
                        self.__file_handles[filenum].write('%s' %(self.__operand_stack.pop()))
                    else:
                        print(self.__operand_stack.pop(), end='')

        # Final newline
        if fileIO:
            self.__file_handles[filenum].write("\n")
        else:
            print()
        self.__prnt_column = 0

    def __letstmt(self):
        """Parses a LET statement,
        consuming the LET keyword.
        """
        self.__advance()  # Advance past the LET token
        self.__assignmentstmt()

    def __gotostmt(self):
        """Parses a GOTO statement

        :return: A FlowSignal containing the target line number
        of the GOTO

        """
        self.__advance()  # Advance past GOTO token
        self.__expr()

        # Set up and return the flow signal
        return FlowSignal(ftarget=self.__operand_stack.pop())

    def __gosubstmt(self):
        """Parses a GOSUB statement

        :return: A FlowSignal containing the first line number
        of the subroutine

        """

        self.__advance()  # Advance past GOSUB token
        self.__expr()

        # Set up and return the flow signal
        return FlowSignal(ftarget=self.__operand_stack.pop(),
                          ftype=FlowSignal.GOSUB)

    def __returnstmt(self):
        """Parses a RETURN statement"""

        self.__advance()  # Advance past RETURN token

        # Set up and return the flow signal
        return FlowSignal(ftype=FlowSignal.RETURN)

    def __stopstmt(self):
        """Parses a STOP statement"""

        self.__advance()  # Advance past STOP token

        for handles in self.__file_handles:
            self.__file_handles[handles].close()
        self.__file_handles.clear()

        return FlowSignal(ftype=FlowSignal.STOP)

    def __assignmentstmt(self):
        """Parses an assignment statement,
        placing the corresponding
        variable and its value in the symbol
        table.

        """
        left = self.__token.lexeme  # Save lexeme of
                                    # the current token
        self.__advance()

        if self.__token.category == Token.LEFTPAREN:
            # We are assigning to an array
            self.__arrayassignmentstmt(left)

        else:
            # We are assigning to a simple variable
            self.__consume(Token.ASSIGNOP)
            self.__logexpr()

            # Check that we are using the right variable name format
            right = self.__operand_stack.pop()

            if left.endswith('$') and not isinstance(right, str):
                raise SyntaxError('Syntax error: Attempt to assign non string to string variable' +
                                  ' in line ' + str(self.__line_number))

            elif not left.endswith('$') and isinstance(right, str):
                raise SyntaxError('Syntax error: Attempt to assign string to numeric variable' +
                                  ' in line ' + str(self.__line_number))

            self.__symbol_table[left] = right

    def __dimstmt(self):
        """Parses  DIM statement and creates a symbol
        table entry for an array of the specified
        dimensions.

        """
        self.__advance()  # Advance past DIM keyword

        # MSBASIC: allow dims of multiple arrays delimited by commas
        while True:
            # Extract the array name, append a suffix so
            # that we can distinguish from simple variables
            # in the symbol table
            name = self.__token.lexeme + '_array'
            self.__advance()  # Advance past array name

            self.__consume(Token.LEFTPAREN)

            # Extract the dimensions
            dimensions = []
            if not self.__tokenindex >= len(self.__tokenlist):
                self.__expr()
                dimensions.append(self.__operand_stack.pop())

                while self.__token.category == Token.COMMA:
                    self.__advance()  # Advance past comma
                    self.__expr()
                    dimensions.append(self.__operand_stack.pop())

            self.__consume(Token.RIGHTPAREN)

            if len(dimensions) > 3:
                raise SyntaxError(
                    'Maximum number of array dimensions is three '
                    + 'in line '
                    + str(self.__line_number)
                )

            # Ensure array is initialised with correct values
            # depending upon type
            if name.endswith('$_array'):
                self.__symbol_table[name] = BASICArray(dimensions, 'str')
            else:
                self.__symbol_table[name] = BASICArray(dimensions, 'num')

            if self.__tokenindex == len(self.__tokenlist):
                # We have parsed the last token here...
                return
            else:
                self.__consume(Token.COMMA)


    def __arrayassignmentstmt(self, name):
        """Parses an assignment to an array variable

        :param name: Array name

        """
        self.__consume(Token.LEFTPAREN)

        # Capture the index variables
        # Extract the dimensions
        indexvars = []
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__expr()
            indexvars.append(self.__operand_stack.pop())

            while self.__token.category == Token.COMMA:
                self.__advance()  # Advance past comma
                self.__expr()
                indexvars.append(self.__operand_stack.pop())

        try:
            BASICarray = self.__symbol_table[name + '_array']

        except KeyError:
            raise KeyError('Array could not be found in line ' +
                           str(self.__line_number))

        if BASICarray.dims != len(indexvars):
            raise IndexError('Incorrect number of indices applied to array ' +
                             'in line ' + str(self.__line_number))

        self.__consume(Token.RIGHTPAREN)
        self.__consume(Token.ASSIGNOP)

        self.__logexpr()

        # Check that we are using the right variable name format
        right = self.__operand_stack.pop()

        if name.endswith('$') and not isinstance(right, str):
            raise SyntaxError('Attempt to assign non string to string array' +
                              ' in line ' + str(self.__line_number))

        elif not name.endswith('$') and isinstance(right, str):
            raise SyntaxError('Attempt to assign string to numeric array' +
                              ' in line ' + str(self.__line_number))

        # Assign to the specified array index
        try:
            if len(indexvars) == 1:
                BASICarray.data[indexvars[0]] = right

            elif len(indexvars) == 2:
                BASICarray.data[indexvars[0]][indexvars[1]] = right

            elif len(indexvars) == 3:
                BASICarray.data[indexvars[0]][indexvars[1]][indexvars[2]] = right

        except IndexError:
            raise IndexError('Array index out of range in line ' +
                             str(self.__line_number))

    def __openstmt(self):
        """Parses an open statement, opens the indicated file and
        places the file handle into handle table
        """

        self.__advance() # Advance past OPEN token

        # Acquire the filename
        self.__logexpr()
        filename = self.__operand_stack.pop()

        # Process the FOR keyword
        self.__consume(Token.FOR)

        if self.__token.category == Token.INPUT:
            accessMode = "r"
        elif self.__token.category == Token.APPEND:
            accessMode = "r+"
        elif self.__token.category == Token.OUTPUT:
            accessMode = "w+"
        else:
            raise SyntaxError('Invalid Open access mode in line ' + str(self.__line_number))

        self.__advance() # Advance past access type

        if self.__token.lexeme != "AS":
            raise SyntaxError('Expecting AS in line ' + str(self.__line_number))

        self.__advance() # Advance past AS keyword

        # Process the # keyword
        self.__consume(Token.HASH)

        # Acquire the file number
        self.__expr()
        filenum = self.__operand_stack.pop()

        branchOnError = False
        if self.__token.category == Token.ELSE:
            branchOnError = True
            self.__advance() # Advance past ELSE

            if self.__token.category == Token.GOTO:
                self.__advance()    # Advance past optional GOTO

            self.__expr()

        if self.__file_handles.get(filenum) != None:
            if branchOnError:
                return FlowSignal(ftarget=self.__operand_stack.pop())
            else:
                raise RuntimeError("File #",filenum," already opened in line " + str(self.__line_number))

        try:
            self.__file_handles[filenum] = open(filename,accessMode)

        except:
            if branchOnError:
                return FlowSignal(ftarget=self.__operand_stack.pop())
            else:
                raise RuntimeError('File '+filename+' could not be opened in line ' + str(self.__line_number))

        if accessMode == "r+":
            self.__file_handles[filenum].seek(0)
            filelen = 0
            for lines in self.__file_handles[filenum]:
                filelen += len(lines)+1

            self.__file_handles[filenum].seek(filelen)

        return None

    def __closestmt(self):
        """Parses a close, closes the file and removes
        the file handle from the handle table
        """

        self.__advance() # Advance past CLOSE token

        # Process the # keyword
        self.__consume(Token.HASH)

        # Acquire the file number
        self.__expr()
        filenum = self.__operand_stack.pop()

        if self.__file_handles.get(filenum) == None:
            raise RuntimeError("CLOSE: file #"+str(filenum)+" not opened in line " + str(self.__line_number))

        self.__file_handles[filenum].close()
        self.__file_handles.pop(filenum)

    def __fseekstmt(self):
        """Parses an fseek statement, seeks the indicated file position
        """

        self.__advance() # Advance past FSEEK token

        # Process the # keyword
        self.__consume(Token.HASH)

        # Acquire the file number
        self.__expr()
        filenum = self.__operand_stack.pop()

        if self.__file_handles.get(filenum) == None:
            raise RuntimeError("FSEEK: file #"+str(filenum)+" not opened in line " + str(self.__line_number))

        # Process the comma
        self.__consume(Token.COMMA)

        # Acquire the file position
        self.__expr()

        self.__file_handles[filenum].seek(self.__operand_stack.pop())

    def __inputstmt(self):
        """Parses an input statement, extracts the input
        from the user and places the values into the
        symbol table

        """
        self.__advance()  # Advance past INPUT token

        fileIO = False
        if self.__token.category == Token.HASH:
            fileIO = True

            # Process the # keyword
            self.__consume(Token.HASH)

            # Acquire the file number
            self.__expr()
            filenum = self.__operand_stack.pop()

            if self.__file_handles.get(filenum) == None:
                raise RuntimeError("INPUT: file #"+str(filenum)+" not opened in line " + str(self.__line_number))

            # Process the comma
            self.__consume(Token.COMMA)

        prompt = '? '
        if self.__token.category == Token.STRING:
            if fileIO:
                raise SyntaxError('Input prompt specified for file I/O ' +
                                'in line ' + str(self.__line_number))

            # Acquire the input prompt
            self.__logexpr()
            prompt = self.__operand_stack.pop()
            self.__consume(Token.SEMICOLON)

        # Acquire the comma separated input variables
        variables = []
        if not self.__tokenindex >= len(self.__tokenlist):
            if self.__token.category != Token.NAME:
                raise ValueError('Expecting NAME in INPUT statement ' +
                                 'in line ' + str(self.__line_number))
            variables.append(self.__token.lexeme)
            self.__advance()  # Advance past variable

            while self.__token.category == Token.COMMA:
                self.__advance()  # Advance past comma
                variables.append(self.__token.lexeme)
                self.__advance()  # Advance past variable

        valid_input = False
        while not valid_input:
            # Gather input from the user into the variables
            if fileIO:
                inputvals = ((self.__file_handles[filenum].readline().replace("\n","")).replace("\r","")).split(',', (len(variables)-1))
                valid_input = True
            else:
                inputvals = input(prompt).split(',', (len(variables)-1))

            for variable in variables:
                left = variable

                try:
                    right = inputvals.pop(0)

                    if left.endswith('$'):
                        self.__symbol_table[left] = str(right)
                        valid_input = True

                    elif not left.endswith('$'):
                        try:
                            if '.' in right:
                                self.__symbol_table[left] = float(right)

                            else:
                                self.__symbol_table[left] = int(right)

                            valid_input = True

                        except ValueError:
                            if not fileIO:
                                valid_input = False
                            print('Non-numeric input provided to a numeric variable - redo from start')
                            break

                except IndexError:
                    # No more input to process
                    if not fileIO:
                        valid_input = False
                    print('Not enough values input - redo from start')
                    break

    def __restorestmt(self):

        self.__advance() # Advance past RESTORE token

        # Acquire the line number
        self.__expr()

        self.__data_values.clear()
        self.__data.restore(self.__operand_stack.pop())

    def __datastmt(self):
        """Parses a DATA statement"""

    def __readstmt(self):
        """Parses a READ statement."""

        self.__advance()  # Advance past READ token

        # Acquire the comma separated input variables
        variables = []
        if not self.__tokenindex >= len(self.__tokenlist):
            variables.append(self.__token.lexeme)
            self.__advance()  # Advance past variable

            while self.__token.category == Token.COMMA:
                self.__advance()  # Advance past comma
                variables.append(self.__token.lexeme)
                self.__advance()  # Advance past variable

        # Gather input from the DATA statement into the variables
        for variable in variables:

            if len(self.__data_values) < 1:
                self.__data_values = self.__data.readData(self.__line_number)

            left = variable
            right = self.__data_values.pop(0)

            if left.endswith('$'):
                # Python inserts quotes around input data
                if isinstance(right, int):
                    raise ValueError('Non-string input provided to a string variable ' +
                                     'in line ' + str(self.__line_number))

                else:
                    self.__symbol_table[left] = right

            elif not left.endswith('$'):
                try:
                    numeric = float(right)
                    if int(numeric) == numeric:
                        numeric = int(numeric)
                    self.__symbol_table[left] = numeric

                except ValueError:
                    raise ValueError('Non-numeric input provided to a numeric variable ' +
                                     'in line ' + str(self.__line_number))

    def __expr(self):
        """Parses a numerical expression consisting
        of two terms being added or subtracted,
        leaving the result on the operand stack.

        """
        self.__term()  # Pushes value of left term
                       # onto top of stack

        while self.__token.category in [Token.PLUS, Token.MINUS]:
            savedcategory = self.__token.category
            self.__advance()
            self.__term()  # Pushes value of right term
                           # onto top of stack
            rightoperand = self.__operand_stack.pop()
            leftoperand = self.__operand_stack.pop()

            if savedcategory == Token.PLUS:
                self.__operand_stack.append(leftoperand + rightoperand)

            else:
                self.__operand_stack.append(leftoperand - rightoperand)

    def __term(self):
        """Parses a numerical expression consisting
        of two factors being multiplied together,
        leaving the result on the operand stack.

        """
        self.__sign = 1  # Initialise sign to keep track of unary
                         # minuses
        self.__factor()  # Leaves value of term on top of stack

        while self.__token.category in [Token.TIMES, Token.DIVIDE, Token.MODULO]:
            savedcategory = self.__token.category
            self.__advance()
            self.__sign = 1  # Initialise sign
            self.__factor()  # Leaves value of term on top of stack
            rightoperand = self.__operand_stack.pop()
            leftoperand = self.__operand_stack.pop()

            if savedcategory == Token.TIMES:
                self.__operand_stack.append(leftoperand * rightoperand)

            elif savedcategory == Token.DIVIDE:
                self.__operand_stack.append(leftoperand / rightoperand)

            else:
                self.__operand_stack.append(leftoperand % rightoperand)

    def __factor(self):
        """Evaluates a numerical expression
        and leaves its value on top of the
        operand stack.

        """
        if self.__token.category == Token.PLUS:
            self.__advance()
            self.__factor()

        elif self.__token.category == Token.MINUS:
            self.__sign = -self.__sign
            self.__advance()
            self.__factor()

        elif self.__token.category == Token.UNSIGNEDINT:
            self.__operand_stack.append(self.__sign*int(self.__token.lexeme))
            self.__advance()

        elif self.__token.category == Token.UNSIGNEDFLOAT:
            self.__operand_stack.append(self.__sign*float(self.__token.lexeme))
            self.__advance()

        elif self.__token.category == Token.STRING:
            self.__operand_stack.append(self.__token.lexeme)
            self.__advance()

        elif (
            self.__token.category == Token.NAME
            and self.__token.category not in Token.functions
        ):
            # Check if this is a simple or array variable
            # MSBASIC Allows simple and complex variables to have the
            # same id.  This is probably a bad idea, but it's used in
            # some old example programs.  So check if next token is parens
            if (
                (self.__token.lexeme + "_array") in self.__symbol_table
                and self.__tokenindex < len(self.__tokenlist) - 1
                and self.__tokenlist[self.__tokenindex + 1].category == Token.LEFTPAREN
            ):
                # Capture the current lexeme
                arrayname = self.__token.lexeme + "_array"

                # Array must be processed
                # Capture the index variables
                self.__advance()  # Advance past the array name

                try:
                    self.__consume(Token.LEFTPAREN)
                    indexvars = []
                    if not self.__tokenindex >= len(self.__tokenlist):
                        self.__expr()
                        indexvars.append(self.__operand_stack.pop())

                        while self.__token.category == Token.COMMA:
                            self.__advance()  # Advance past comma
                            self.__expr()
                            indexvars.append(self.__operand_stack.pop())

                    BASICarray = self.__symbol_table[arrayname]
                    arrayval = self.__get_array_val(BASICarray, indexvars)

                    if arrayval != None:
                        self.__operand_stack.append(self.__sign * arrayval)

                    else:
                        raise IndexError(
                            "Empty array value returned in line "
                            + str(self.__line_number)
                        )
                except RuntimeError:
                    raise RuntimeError(
                        "Array used without index in line " + str(self.__line_number)
                    )

            elif self.__token.lexeme in self.__symbol_table:
                # Simple variable must be processed
                self.__operand_stack.append(self.__sign*self.__symbol_table[self.__token.lexeme])

            else:
                raise RuntimeError('Name ' + self.__token.lexeme + ' is not defined' +
                                   ' in line ' + str(self.__line_number))

            self.__advance()

        elif self.__token.category == Token.LEFTPAREN:
            self.__advance()

            # Save sign because expr() calls term() which resets
            # sign to 1
            savesign = self.__sign
            self.__logexpr()  # Value of expr is pushed onto stack

            if savesign == -1:
                # Change sign of expression
                self.__operand_stack[-1] = -self.__operand_stack[-1]

            self.__consume(Token.RIGHTPAREN)

        elif self.__token.category in Token.functions:
            self.__operand_stack.append(self.__evaluate_function(self.__token.category))

        else:
            raise RuntimeError('Expecting factor in numeric expression' +
                               ' in line ' + str(self.__line_number) +
                               self.__token.lexeme)

    def __get_array_val(self, BASICarray, indexvars):
        """Extracts the value from the given BASICArray at the specified indexes

        :param BASICarray: The BASICArray
        :param indexvars: The list of indexes, one for each dimension

        :return: The value at the indexed position in the array

        """
        if BASICarray.dims != len(indexvars):
            raise IndexError('Incorrect number of indices applied to array ' +
                             'in line ' + str(self.__line_number))

        # Fetch the value from the array
        try:
            if len(indexvars) == 1:
                arrayval = BASICarray.data[indexvars[0]]

            elif len(indexvars) == 2:
                arrayval = BASICarray.data[indexvars[0]][indexvars[1]]

            elif len(indexvars) == 3:
                arrayval = BASICarray.data[indexvars[0]][indexvars[1]][indexvars[2]]

        except IndexError:
            raise IndexError('Array index out of range in line ' +
                             str(self.__line_number))

        return arrayval

    def __compoundstmt(self):
        """Parses compound statements,
        specifically if-then-else and
        loops

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """
        if self.__token.category == Token.FOR:
            return self.__forstmt()

        elif self.__token.category == Token.NEXT:
            return self.__nextstmt()

        elif self.__token.category == Token.IF:
            return self.__ifstmt()

        elif self.__token.category == Token.ON:
            return self.__ongosubstmt()

    def __ifstmt(self):
        """Parses if-then-else
        statements

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """

        self.__advance()  # Advance past IF token
        self.__logexpr()

        # Save result of expression
        saveval = self.__operand_stack.pop()

        # Process the THEN part and save the jump value
        self.__consume(Token.THEN)

        if self.__token.category != Token.UNSIGNEDINT:
            if saveval:
                return FlowSignal(ftype=FlowSignal.EXECUTE)
        else:
            self.__expr()

            # Jump if the expression evaluated to True
            if saveval:
                # Set up and return the flow signal
                return FlowSignal(ftarget=self.__operand_stack.pop())

        # advance to ELSE
        while self.__tokenindex < len(self.__tokenlist) and self.__token.category != Token.ELSE:
            self.__advance()

        # See if there is an ELSE part
        if self.__token.category == Token.ELSE:
            self.__advance()

            if self.__token.category != Token.UNSIGNEDINT:
                return FlowSignal(ftype=FlowSignal.EXECUTE)
            else:

                self.__expr()

                # Set up and return the flow signal
                return FlowSignal(ftarget=self.__operand_stack.pop())

        else:
            # No ELSE action
            return None

    def __forstmt(self):
        """Parses for loops

        :return: The FlowSignal to indicate that
        a loop start has been processed

        """

        # Set up default loop increment value
        step = 1

        self.__advance()  # Advance past FOR token

        # Process the loop variable initialisation
        loop_variable = self.__token.lexeme  # Save lexeme of
                                             # the current token

        if loop_variable.endswith('$'):
            raise SyntaxError('Syntax error: Loop variable is not numeric' +
                              ' in line ' + str(self.__line_number))

        self.__advance()  # Advance past loop variable
        self.__consume(Token.ASSIGNOP)
        self.__expr()

        # Check that we are using the right variable name format
        # for numeric variables
        start_val = self.__operand_stack.pop()

        # Advance past the 'TO' keyword
        self.__consume(Token.TO)

        # Process the terminating value
        self.__expr()
        end_val = self.__operand_stack.pop()

        # Check if there is a STEP value
        increment = True
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__consume(Token.STEP)

            # Acquire the step value
            self.__expr()
            step = self.__operand_stack.pop()

            # Check whether we are decrementing or
            # incrementing
            if step == 0:
                raise IndexError('Zero step value supplied for loop' +
                                 ' in line ' + str(self.__line_number))

            elif step < 0:
                increment = False

        # Now determine the status of the loop

        # Note that we cannot use the presence of the loop variable in
        # the symbol table for this test, as the same variable may already
        # have been instantiated elsewhere in the program
        #
        # Need to initialize the loop variable anytime the for
        # statement is reached from a statement other than an active NEXT.

        from_next = False
        if self.last_flowsignal:
            if self.last_flowsignal.ftype == FlowSignal.LOOP_REPEAT:
                from_next = True

        if not from_next:
            self.__symbol_table[loop_variable] = start_val

        else:
            # We need to modify the loop variable
            # according to the STEP value
            self.__symbol_table[loop_variable] += step

        # If the loop variable has reached the end value,
        # remove it from the set of extant loop variables to signal that
        # this is the last loop iteration
        stop = False
        if increment and self.__symbol_table[loop_variable] > end_val:
            stop = True

        elif not increment and self.__symbol_table[loop_variable] < end_val:
            stop = True

        if stop:
            # Loop must terminate
            return FlowSignal(ftype=FlowSignal.LOOP_SKIP,
                              ftarget=loop_variable)
        else:
            # Set up and return the flow signal
            return FlowSignal(ftype=FlowSignal.LOOP_BEGIN,floop_var=loop_variable)

    def __nextstmt(self):
        """Processes a NEXT statement that terminates
        a loop

        :return: A FlowSignal indicating that a loop
        has been processed

        """

        self.__advance()  # Advance past NEXT token

        # Process the loop variable initialisation
        loop_variable = self.__token.lexeme  # Save lexeme of
                                             # the current token

        if loop_variable.endswith('$'):
            raise SyntaxError('Syntax error: Loop variable is not numeric' +
                              ' in line ' + str(self.__line_number))

        return FlowSignal(ftype=FlowSignal.LOOP_REPEAT,floop_var=loop_variable)

    def __ongosubstmt(self):
        """Process the ON-GOSUB statement

        :return: A FlowSignal indicating the subroutine line number
        if the condition is true, None otherwise

        """

        self.__advance()  # Advance past ON token
        self.__expr()

        # Save result of expression
        saveval = self.__operand_stack.pop()

        if self.__token.category == Token.GOTO:
            self.__consume(Token.GOTO)
            branchtype = 1
        else:
            self.__consume(Token.GOSUB)
            branchtype = 2

        branch_values = []
        # Acquire the comma separated values
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__expr()
            branch_values.append(self.__operand_stack.pop())

            while self.__token.category == Token.COMMA:
                self.__advance()  # Advance past comma
                self.__expr()
                branch_values.append(self.__operand_stack.pop())

        if saveval < 1 or saveval > len(branch_values) or len(branch_values) == 0:
            return None
        elif branchtype == 1:
            return FlowSignal(ftarget=branch_values[saveval-1])
        else:
            return FlowSignal(ftarget=branch_values[saveval-1],
                              ftype=FlowSignal.GOSUB)

    def __relexpr(self):
        """Parses a relational expression
        """
        self.__expr()

        # Since BASIC uses same operator for both
        # assignment and equality, we need to check for this
        if self.__token.category == Token.ASSIGNOP:
            self.__token.category = Token.EQUAL

        if self.__token.category in [Token.LESSER, Token.LESSEQUAL,
                              Token.GREATER, Token.GREATEQUAL,
                              Token.EQUAL, Token.NOTEQUAL]:
            savecat = self.__token.category
            self.__advance()
            self.__expr()

            right = self.__operand_stack.pop()
            left = self.__operand_stack.pop()

            if savecat == Token.EQUAL:
                self.__operand_stack.append(left == right)  # Push True or False

            elif savecat == Token.NOTEQUAL:
                self.__operand_stack.append(left != right)  # Push True or False

            elif savecat == Token.LESSER:
                self.__operand_stack.append(left < right)  # Push True or False

            elif savecat == Token.GREATER:
                self.__operand_stack.append(left > right)  # Push True or False

            elif savecat == Token.LESSEQUAL:
                self.__operand_stack.append(left <= right)  # Push True or False

            elif savecat == Token.GREATEQUAL:
                self.__operand_stack.append(left >= right)  # Push True or False

    def __logexpr(self):
        """Parses a logical expression
        """
        self.__notexpr()

        while self.__token.category in [Token.OR, Token.AND]:
            savecat = self.__token.category
            self.__advance()
            self.__notexpr()

            right = self.__operand_stack.pop()
            left = self.__operand_stack.pop()

            if savecat == Token.OR:
                self.__operand_stack.append(left or right)  # Push True or False

            elif savecat == Token.AND:
                self.__operand_stack.append(left and right)  # Push True or False

    def __notexpr(self):
        """Parses a logical not expression
        """
        if self.__token.category == Token.NOT:
            self.__advance()
            self.__relexpr()
            right = self.__operand_stack.pop()
            self.__operand_stack.append(not right)
        else:
            self.__relexpr()

    def __evaluate_function(self, category):
        """Evaluate the function in the statement
        and return the result.

        :return: The result of the function

        """

        self.__advance()  # Advance past function name

        # Process arguments according to function
        if category == Token.RND:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            arg = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)
            # MSBASIC basic reseeds with negative values
            # as arg to RND... not sure if it returned anything
            # Zero returns the last value again (not implemented)
            # Any positive value returns random fload btw 0 and 1
            if arg < 0:
                random.seed(arg)

            return random.random()

        if category == Token.PI:
            return math.pi

        if category == Token.RNDINT:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            lo = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            hi = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)

            try:
                return random.randint(lo, hi)

            except ValueError:
                raise ValueError("Invalid value supplied to RNDINT in line " +
                                 str(self.__line_number))

        if category == Token.MAX:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            value_list = [self.__operand_stack.pop()]

            while self.__token.category == Token.COMMA:
                self.__advance() # Advance past comma
                self.__expr()
                value_list.append(self.__operand_stack.pop())

            self.__consume(Token.RIGHTPAREN)

            try:
                return max(*value_list)

            except TypeError:
                raise TypeError("Invalid type supplied to MAX in line " +
                                 str(self.__line_number))

        if category == Token.MIN:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            value_list = [self.__operand_stack.pop()]

            while self.__token.category == Token.COMMA:
                self.__advance() # Advance past comma
                self.__expr()
                value_list.append(self.__operand_stack.pop())

            self.__consume(Token.RIGHTPAREN)

            try:
                return min(*value_list)

            except TypeError:
                raise TypeError("Invalid type supplied to MIN in line " +
                                 str(self.__line_number))

        if category == Token.POW:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            base = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            exponent = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)

            try:
                return math.pow(base, exponent)

            except ValueError:
                raise ValueError("Invalid value supplied to POW in line " +
                                 str(self.__line_number))

        if category == Token.TERNARY:
            self.__consume(Token.LEFTPAREN)

            self.__logexpr()
            condition = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            whentrue = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            whenfalse = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)

            return whentrue if condition else whenfalse

        if category == Token.LEFT:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            instring = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            chars = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)

            try:
                return instring[:chars]

            except TypeError:
                raise TypeError("Invalid type supplied to LEFT$ in line " +
                                 str(self.__line_number))

        if category == Token.RIGHT:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            instring = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            chars = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)

            try:
                return instring[-chars:]

            except TypeError:
                raise TypeError("Invalid type supplied to RIGHT$ in line " +
                                 str(self.__line_number))

        if category == Token.MID:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            instring = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            # Older basic dialets were always 1 based
            start = self.__operand_stack.pop() - 1

            if self.__token.category == Token.COMMA:
                self.__advance() # Advance past comma
                self.__expr()
                chars = self.__operand_stack.pop()
            else:
                chars = None

            self.__consume(Token.RIGHTPAREN)

            try:
                if chars:
                    return instring[start:start+chars]
                else:
                    return instring[start:]

            except TypeError:
                raise TypeError("Invalid type supplied to MID$ in line " +
                                 str(self.__line_number))

        if category == Token.INSTR:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            hackstackstring = self.__operand_stack.pop()
            if not isinstance(hackstackstring, str):
                raise TypeError("Invalid type supplied to INSTR in line " +
                                 str(self.__line_number))

            self.__consume(Token.COMMA)

            self.__expr()
            needlestring = self.__operand_stack.pop()

            start = end = None
            if self.__token.category == Token.COMMA:
                self.__advance() # Advance past comma
                self.__expr()
                # Older basic dialets were always 1 based
                start = self.__operand_stack.pop() -1

                if self.__token.category == Token.COMMA:
                    self.__advance() # Advance past comma
                    self.__expr()
                    end = self.__operand_stack.pop() -1

            self.__consume(Token.RIGHTPAREN)

            try:
                # Older basis dialets are 1 based, so the return value
                # here needs to be incremented by one.  ALSO
                # this moves the -1 not found value to 0
                # which indicated not found in most dialects
                return hackstackstring.find(needlestring, start, end) + 1

            except TypeError:
                raise TypeError("Invalid type supplied to INSTR in line " +
                                 str(self.__line_number))

        self.__consume(Token.LEFTPAREN)

        self.__expr()
        value = self.__operand_stack.pop()

        self.__consume(Token.RIGHTPAREN)

        if category == Token.SQR:
            try:
                return math.sqrt(value)

            except ValueError:
                raise ValueError("Invalid value supplied to SQR in line " +
                                 str(self.__line_number))

        elif category == Token.ABS:
            try:
                return abs(value)

            except ValueError:
                raise ValueError("Invalid value supplied to ABS in line " +
                                 str(self.__line_number))

        elif category == Token.ATN:
            try:
                return math.atan(value)

            except ValueError:
                raise ValueError("Invalid value supplied to ATN in line " +
                                 str(self.__line_number))

        elif category == Token.COS:
            try:
                return math.cos(value)

            except ValueError:
                raise ValueError("Invalid value supplied to COS in line " +
                                 str(self.__line_number))

        elif category == Token.EXP:
            try:
                return math.exp(value)

            except ValueError:
                raise ValueError("Invalid value supplied to EXP in line " +
                                 str(self.__line_number))

        elif category == Token.INT:
            try:
                return math.floor(value)

            except ValueError:
                raise ValueError("Invalid value supplied to INT in line " +
                                 str(self.__line_number))

        elif category == Token.ROUND:
            try:
                return round(value)

            except TypeError:
                raise TypeError("Invalid type supplied to LEN in line " +
                                 str(self.__line_number))

        elif category == Token.LOG:
            try:
                return math.log(value)

            except ValueError:
                raise ValueError("Invalid value supplied to LOG in line " +
                                 str(self.__line_number))

        elif category == Token.SIN:
            try:
                return math.sin(value)

            except ValueError:
                raise ValueError("Invalid value supplied to SIN in line " +
                                 str(self.__line_number))

        elif category == Token.TAN:
            try:
                return math.tan(value)

            except ValueError:
                raise ValueError("Invalid value supplied to TAN in line " +
                                 str(self.__line_number))

        elif category == Token.CHR:
            try:
                return chr(value)

            except TypeError:
                raise TypeError("Invalid type supplied to CHR$ in line " +
                                 str(self.__line_number))

            except ValueError:
                raise ValueError("Invalid value supplied to CHR$ in line " +
                                 str(self.__line_number))

        elif category == Token.ASC:
            try:
                return ord(value)

            except TypeError:
                raise TypeError("Invalid type supplied to ASC in line " +
                                 str(self.__line_number))

            except ValueError:
                raise ValueError("Invalid value supplied to ASC in line " +
                                 str(self.__line_number))

        elif category == Token.STR:
            return str(value)

        elif category == Token.VAL:
            try:
                numeric = float(value)
                if int(numeric) == numeric:
                    return int(numeric)
                return numeric

            # Like other BASIC variants, non-numeric strings return 0
            except ValueError:
                return 0

        elif category == Token.LEN:
            try:
                return len(value)

            except TypeError:
                raise TypeError("Invalid type supplied to LEN in line " +
                                 str(self.__line_number))

        elif category == Token.UPPER:
            if not isinstance(value, str):
                raise TypeError("Invalid type supplied to UPPER$ in line " +
                                 str(self.__line_number))

            return value.upper()

        elif category == Token.LOWER:
            if not isinstance(value, str):
                raise TypeError("Invalid type supplied to LOWER$ in line " +
                                 str(self.__line_number))

            return value.lower()

        elif category == Token.TAB:
            if isinstance(value, int):
                return " "*value

            else:
                raise TypeError("Invalid type supplied to TAB in line " +
                                 str(self.__line_number))

        else:
            raise SyntaxError("Unrecognised function in line " +
                              str(self.__line_number))

    def __randomizestmt(self):
        """Implements a function to seed the random
        number generator

        """
        self.__advance()  # Advance past RANDOMIZE token

        if not self.__tokenindex >= len(self.__tokenlist):
            self.__expr()  # Process the seed
            seed = self.__operand_stack.pop()

            random.seed(seed)

        else:
            random.seed(int(monotonic()))

class BASICData:

    def __init__(self):
        # array of line numbers to represent data statements
        self.__datastmts = {}

        # Data pointer
        self.__next_data = 0


    def delete(self):
        self.__datastmts.clear()
        self.__next_data = 0

    def delData(self,line_number):
        if self.__datastmts.get(line_number) != None:
            del self.__datastmts[line_number]

    def addData(self,line_number,tokenlist):
        """
        Adds the supplied token list
        to the program's DATA store. If a token list with the
        same line number already exists, this is
        replaced.

        line_number: Basic program line number of DATA statement

        """

        try:
            self.__datastmts[line_number] = tokenlist

        except TypeError as err:
            raise TypeError("Invalid line number: " + str(err))


    def getTokens(self,line_number):
        """
        returns the tokens from the program DATA statement

        line_number: Basic program line number of DATA statement

        """

        return self.__datastmts.get(line_number)

    def readData(self,read_line_number):

        if len(self.__datastmts) == 0:
            raise RuntimeError('No DATA statements available to READ ' +
                               'in line ' + str(read_line_number))

        data_values = []

        line_numbers = list(self.__datastmts.keys())
        line_numbers.sort()

        if self.__next_data == 0:
            self.__next_data = line_numbers[0]
        elif line_numbers.index(self.__next_data) < len(line_numbers)-1:
            self.__next_data = line_numbers[line_numbers.index(self.__next_data)+1]
        else:
            raise RuntimeError('No DATA statements available to READ ' +
                               'in line ' + str(read_line_number))

        tokenlist = self.__datastmts[self.__next_data]

        sign = 1
        for token in tokenlist[1:]:
            if token.category != Token.COMMA:
                #data_values.append(token.lexeme)

                if token.category == Token.STRING:
                    data_values.append(token.lexeme)
                elif token.category == Token.UNSIGNEDINT:
                    data_values.append(sign*int(token.lexeme))
                elif token.category == Token.UNSIGNEDFLOAT:
                    data_values.append(sign*eval(token.lexeme))
                elif token.category == Token.MINUS:
                    sign = -1
                #else:
                    #data_values.append(token.lexeme)
            else:
                sign = 1


        return data_values

    def restore(self,restoreLineNo):
        if restoreLineNo == 0 or restoreLineNo in self.__datastmts:

            if restoreLineNo == 0:
                self.__next_data = restoreLineNo
            else:

                line_numbers = list(self.__datastmts.keys())
                line_numbers.sort()

                indexln = line_numbers.index(restoreLineNo)

                if indexln == 0:
                    self.__next_data = 0
                else:
                    self.__next_data = line_numbers[indexln-1]
        else:
            raise RuntimeError('Attempt to RESTORE but no DATA ' +
                               'statement at line ' + str(restoreLineNo))


class Program:

    def __init__(self):
        # Dictionary to represent program
        # statements, keyed by line number
        self.__program = {}

        # Program counter
        self.__next_stmt = 0

        # Initialise return stack for subroutine returns
        self.__return_stack = []

        # return dictionary for loop returns
        self.__return_loop = {}

        # Setup DATA object
        self.__data = BASICData()

    def __str__(self):

        program_text = ""
        line_numbers = self.line_numbers()

        for line_number in line_numbers:
            program_text += self.str_statement(line_number)

        return program_text

    def str_statement(self, line_number):
        line_text = str(line_number) + " "

        statement = self.__program[line_number]
        if statement[0].category == Token.DATA:
            statement = self.__data.getTokens(line_number)
        for token in statement:
            # Add in quotes for strings
            if token.category == Token.STRING:
                line_text += '"' + token.lexeme + '" '

            else:
                line_text += token.lexeme + " "
        line_text += "\n"
        return line_text

    def list(self, start_line=None, end_line=None):
        """Lists the program"""
        line_numbers = self.line_numbers()
        if not start_line:
            start_line = int(line_numbers[0])

        if not end_line:
            end_line = int(line_numbers[-1])

        for line_number in line_numbers:
            if int(line_number) >= start_line and int(line_number) <= end_line:
                print(self.str_statement(line_number), end="")

    def save(self, file):
        """Save the program

        :param file: The name and path of the save file, .bas is
                     appended

        """
        if not file.lower().endswith(".bas"):
            file += ".bas"
        try:
            with open(file, "w") as outfile:
                outfile.write(str(self))
        except OSError:
            raise OSError("Could not save to file")

    def load(self, file):
        """Load the program

        :param file: The name and path of the file to be loaded, .bas is
                     appended

        """

        # New out the program
        self.delete()
        if not file.lower().endswith(".bas"):
            file += ".bas"
        try:
            lexer = Lexer()
            with open(file, "r") as infile:
                for line in infile:
                    line = line.replace("\r", "").replace("\n", "").strip()
                    tokenlist = lexer.tokenize(line)
                    self.add_stmt(tokenlist)

        except OSError:
            raise OSError("Could not read file")

    def add_stmt(self, tokenlist):
        """
        Adds the supplied token list
        to the program. The first token should
        be the line number. If a token list with the
        same line number already exists, this is
        replaced.

        :param tokenlist: List of BTokens representing a
        numbered program statement

        """
        if len(tokenlist) > 0:
            try:
                line_number = int(tokenlist[0].lexeme)
                if tokenlist[1].lexeme == "DATA":
                    self.__data.addData(line_number,tokenlist[1:])
                    self.__program[line_number] = [tokenlist[1],]
                else:
                    self.__program[line_number] = tokenlist[1:]

            except TypeError as err:
                raise TypeError("Invalid line number: " +
                                str(err))

    def line_numbers(self):
        """Returns a list of all the
        line numbers for the program,
        sorted

        :return: A sorted list of
        program line numbers
        """
        line_numbers = list(self.__program.keys())
        line_numbers.sort()

        return line_numbers

    def __execute(self, line_number):
        """Execute the statement with the
        specified line number

        :param line_number: The line number

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """
        if line_number not in self.__program.keys():
            raise RuntimeError("Line number " + line_number +
                               " does not exist")

        statement = self.__program[line_number]

        try:
            return self.__parser.parse(statement, line_number)

        except RuntimeError as err:
            raise RuntimeError(str(err))

    def execute(self):
        """Execute the program"""

        self.__parser = BASICParser(self.__data)
        self.__data.restore(0) # reset data pointer

        line_numbers = self.line_numbers()

        if len(line_numbers) > 0:
            # Set up an index into the ordered list
            # of line numbers that can be used for
            # sequential statement execution. The index
            # will be incremented by one, unless modified by
            # a jump
            index = 0
            self.set_next_line_number(line_numbers[index])

            # Run through the program until the
            # has line number has been reached
            while True:
                flowsignal = self.__execute(self.get_next_line_number())
                self.__parser.last_flowsignal = flowsignal

                if flowsignal:
                    if flowsignal.ftype == FlowSignal.SIMPLE_JUMP:
                        # GOTO or conditional branch encountered
                        try:
                            index = line_numbers.index(flowsignal.ftarget)

                        except ValueError:
                            raise RuntimeError("Invalid line number supplied in GOTO or conditional branch: "
                                               + str(flowsignal.ftarget))

                        self.set_next_line_number(flowsignal.ftarget)

                    elif flowsignal.ftype == FlowSignal.GOSUB:
                        # Subroutine call encountered
                        # Add line number of next instruction to
                        # the return stack
                        if index + 1 < len(line_numbers):
                            self.__return_stack.append(line_numbers[index + 1])

                        else:
                            raise RuntimeError("GOSUB at end of program, nowhere to return")

                        # Set the index to be the subroutine start line
                        # number
                        try:
                            index = line_numbers.index(flowsignal.ftarget)

                        except ValueError:
                            raise RuntimeError("Invalid line number supplied in subroutine call: "
                                               + str(flowsignal.ftarget))

                        self.set_next_line_number(flowsignal.ftarget)

                    elif flowsignal.ftype == FlowSignal.RETURN:
                        # Subroutine return encountered
                        # Pop return address from the stack
                        try:
                            index = line_numbers.index(self.__return_stack.pop())

                        except ValueError:
                            raise RuntimeError("Invalid subroutine return in line " +
                                               str(self.get_next_line_number()))

                        except IndexError:
                            raise RuntimeError("RETURN encountered without corresponding " +
                                               "subroutine call in line " + str(self.get_next_line_number()))

                        self.set_next_line_number(line_numbers[index])

                    elif flowsignal.ftype == FlowSignal.STOP:
                        break

                    elif flowsignal.ftype == FlowSignal.LOOP_BEGIN:
                        # Loop start encountered
                        # Put loop line number on the stack so
                        # that it can be returned to when the loop
                        # repeats
                        self.__return_loop[flowsignal.floop_var] = line_numbers[index]

                        # Continue to the next statement in the loop
                        index = index + 1

                        if index < len(line_numbers):
                            self.set_next_line_number(line_numbers[index])

                        else:
                            # Reached end of program
                            raise RuntimeError("Program terminated within a loop")

                    elif flowsignal.ftype == FlowSignal.LOOP_SKIP:
                        # Loop variable has reached end value, so ignore
                        # all statements within loop and move past the corresponding
                        # NEXT statement
                        index = index + 1
                        while index < len(line_numbers):
                            next_line_number = line_numbers[index]
                            temp_tokenlist = self.__program[next_line_number]

                            if temp_tokenlist[0].category == Token.NEXT and \
                               len(temp_tokenlist) > 1:
                                # Check the loop variable to ensure we have not found
                                # the NEXT statement for a nested loop
                                if temp_tokenlist[1].lexeme == flowsignal.ftarget:
                                    # Move the statement after this NEXT, if there
                                    # is one
                                    index = index + 1
                                    if index < len(line_numbers):
                                        next_line_number = line_numbers[index]  # Statement after the NEXT
                                        self.set_next_line_number(next_line_number)
                                        break

                            index = index + 1

                        # Check we have not reached end of program
                        if index >= len(line_numbers):
                            # Terminate the program
                            break

                    elif flowsignal.ftype == FlowSignal.LOOP_REPEAT:
                        # Loop repeat encountered
                        # Pop the loop start address from the stack
                        try:
                            index = line_numbers.index(self.__return_loop.pop(flowsignal.floop_var))

                        except ValueError:
                            raise RuntimeError("Invalid loop exit in line " +
                                               str(self.get_next_line_number()))

                        except KeyError:
                            raise RuntimeError("NEXT encountered without corresponding " +
                                               "FOR loop in line " + str(self.get_next_line_number()))

                        self.set_next_line_number(line_numbers[index])

                else:
                    index = index + 1

                    if index < len(line_numbers):
                        self.set_next_line_number(line_numbers[index])

                    else:
                        # Reached end of program
                        break

        else:
            raise RuntimeError("No statements to execute")

    def delete(self):
        """Deletes the program by emptying the dictionary"""
        self.__program.clear()
        self.__data.delete()

    def delete_statement(self, line_number):
        """Deletes a statement from the program with
        the specified line number, if it exists

        :param line_number: The line number to be deleted

        """
        self.__data.delData(line_number)
        try:
            del self.__program[line_number]

        except KeyError:
            raise KeyError("Line number does not exist")

    def get_next_line_number(self):
        """Returns the line number of the next statement
        to be executed

        :return: The line number

        """

        return self.__next_stmt

    def set_next_line_number(self, line_number):
        """Sets the line number of the next
        statement to be executed

        :param line_number: The new line number

        """
        self.__next_stmt = line_number

class Token:

        """BASICToken categories"""

        EOF             = 0   # End of file
        LET             = 1   # LET keyword
        LIST            = 2   # LIST command
        PRINT           = 3   # PRINT command
        RUN             = 4   # RUN command
        FOR             = 5   # FOR keyword
        NEXT            = 6   # NEXT keyword
        IF              = 7   # IF keyword
        THEN            = 8   # THEN keyword
        ELSE            = 9   # ELSE keyword
        ASSIGNOP        = 10  # '='
        LEFTPAREN       = 11  # '('
        RIGHTPAREN      = 12  # ')'
        PLUS            = 13  # '+'
        MINUS           = 14  # '-'
        TIMES           = 15  # '*'
        DIVIDE          = 16  # '/'
        NEWLINE         = 17  # End of line
        UNSIGNEDINT     = 18  # Integer
        NAME            = 19  # Identifier that is not a keyword
        EXIT            = 20  # Used to quit the interpreter
        DIM             = 21  # DIM keyword
        GREATER         = 22  # '>'
        LESSER          = 23  # '<'
        STEP            = 24  # STEP keyword
        GOTO            = 25  # GOTO keyword
        GOSUB           = 26  # GOSUB keyword
        INPUT           = 27  # INPUT keyword
        REM             = 28  # REM keyword
        RETURN          = 29  # RETURN keyword
        SAVE            = 30  # SAVE command
        LOAD            = 31  # LOAD command
        NOTEQUAL        = 32  # '<>'
        LESSEQUAL       = 33  # '<='
        GREATEQUAL      = 34  # '>='
        UNSIGNEDFLOAT   = 35  # Floating point number
        STRING          = 36  # String values
        TO              = 37  # TO keyword
        NEW             = 38  # NEW command
        EQUAL           = 39  # '='
        COMMA           = 40  # ','
        STOP            = 41  # STOP keyword
        COLON           = 42  # ':'
        ON              = 43  # ON keyword
        POW             = 44  # Power function
        SQR             = 45  # Square root function
        ABS             = 46  # Absolute value function
        DIM             = 47  # DIM keyword
        RANDOMIZE       = 48  # RANDOMIZE keyword
        RND             = 49  # RND keyword
        ATN             = 50  # Arctangent function
        COS             = 51  # Cosine function
        EXP             = 52  # Exponential function
        LOG             = 53  # Natural logarithm function
        SIN             = 54  # Sine function
        TAN             = 55  # Tangent function
        DATA            = 56  # DATA keyword
        READ            = 57  # READ keyword
        INT             = 58  # INT function
        CHR             = 59  # CHR$ function
        ASC             = 60  # ASC function
        STR             = 61  # STR$ function
        MID             = 62  # MID$ function
        MODULO          = 63  # MODULO operator
        TERNARY         = 64  # TERNARY functions
        VAL             = 65  # VAL function
        LEN             = 66  # LEN function
        UPPER           = 67  # UPPER function
        LOWER           = 68  # LOWER function
        ROUND           = 69  # ROUND function
        MAX             = 70  # MAX function
        MIN             = 71  # MIN function
        INSTR           = 72  # INSTR function
        AND             = 73  # AND operator
        OR              = 74  # OR operator
        NOT             = 75  # NOT operator
        PI              = 76  # PI constant
        RNDINT          = 77  # RNDINT function
        OPEN            = 78  # OPEN keyword
        HASH            = 79  # "#"
        CLOSE           = 80  # CLOSE keyword
        FSEEK           = 81  # FSEEK keyword
        RESTORE         = 82  # RESTORE keyword
        APPEND          = 83  # APPEND keyword
        OUTPUT          = 84  # OUTPUT keyword
        TAB             = 85  # TAB function
        SEMICOLON       = 86  # SEMICOLON
        LEFT            = 87  # LEFT$ function
        RIGHT           = 88  # RIGHT$ function

        # Displayable names for each token category
        catnames = ['EOF', 'LET', 'LIST', 'PRINT', 'RUN',
        'FOR', 'NEXT', 'IF', 'THEN', 'ELSE', 'ASSIGNOP',
        'LEFTPAREN', 'RIGHTPAREN', 'PLUS', 'MINUS', 'TIMES',
        'DIVIDE', 'NEWLINE', 'UNSIGNEDINT', 'NAME', 'EXIT',
        'DIM', 'GREATER', 'LESSER', 'STEP', 'GOTO', 'GOSUB',
        'INPUT', 'REM', 'RETURN', 'SAVE', 'LOAD',
        'NOTEQUAL', 'LESSEQUAL', 'GREATEQUAL',
        'UNSIGNEDFLOAT', 'STRING', 'TO', 'NEW', 'EQUAL',
        'COMMA', 'STOP', 'COLON', 'ON', 'POW', 'SQR', 'ABS',
        'DIM', 'RANDOMIZE', 'RND', 'ATN', 'COS', 'EXP',
        'LOG', 'SIN', 'TAN', 'DATA', 'READ', 'INT',
        'CHR', 'ASC', 'STR', 'MID', 'MODULO', 'TERNARY',
        'VAL', 'LEN', 'UPPER', 'LOWER', 'ROUND',
        'MAX', 'MIN', 'INSTR', 'AND', 'OR', 'NOT', 'PI',
        'RNDINT', 'OPEN', 'HASH', 'CLOSE', 'FSEEK', 'APPEND',
        'OUTPUT', 'RESTORE', 'RNDINT', 'TAB', 'SEMICOLON',
        'LEFT', 'RIGHT']

        smalltokens = {'=': ASSIGNOP, '(': LEFTPAREN, ')': RIGHTPAREN,
                       '+': PLUS, '-': MINUS, '*': TIMES, '/': DIVIDE,
                       '\n': NEWLINE, '<': LESSER,
                       '>': GREATER, '<>': NOTEQUAL,
                       '<=': LESSEQUAL, '>=': GREATEQUAL, ',': COMMA,
                       ':': COLON, '%': MODULO, '!=': NOTEQUAL, '#': HASH,
                       ';': SEMICOLON}


        # Dictionary of BASIC reserved words
        keywords = {'LET': LET, 'LIST': LIST, 'PRINT': PRINT,
                    'FOR': FOR, 'RUN': RUN, 'NEXT': NEXT,
                    'IF': IF, 'THEN': THEN, 'ELSE': ELSE,
                    'EXIT': EXIT, 'DIM': DIM, 'STEP': STEP,
                    'GOTO': GOTO, 'GOSUB': GOSUB,
                    'INPUT': INPUT, 'REM': REM, 'RETURN': RETURN,
                    'SAVE': SAVE, 'LOAD': LOAD, 'NEW': NEW,
                    'STOP': STOP, 'TO': TO, 'ON':ON, 'POW': POW,
                    'SQR': SQR, 'ABS': ABS,
                    'RANDOMIZE': RANDOMIZE, 'RND': RND,
                    'ATN': ATN, 'COS': COS, 'EXP': EXP,
                    'LOG': LOG, 'SIN': SIN, 'TAN': TAN,
                    'DATA': DATA, 'READ': READ, 'INT': INT,
                    'CHR$': CHR, 'ASC': ASC, 'STR$': STR,
                    'MID$': MID, 'MOD': MODULO,
                    'IF$': TERNARY, 'IFF': TERNARY,
                    'VAL': VAL, 'LEN': LEN,
                    'UPPER$': UPPER, 'LOWER$': LOWER,
                    'ROUND': ROUND, 'MAX': MAX, 'MIN': MIN,
                    'INSTR': INSTR, 'END': STOP,
                    'AND': AND, 'OR': OR, 'NOT': NOT,
                    'PI': PI, 'RNDINT': RNDINT, 'OPEN': OPEN,
                    'CLOSE': CLOSE, 'FSEEK': FSEEK,
                    'APPEND': APPEND, 'OUTPUT':OUTPUT,
                    'RESTORE': RESTORE, 'TAB': TAB,
                    'LEFT$': LEFT, 'RIGHT$': RIGHT}


        # Functions
        functions = {ABS, ATN, COS, EXP, INT, LOG, POW, RND, SIN, SQR, TAN,
                     CHR, ASC, MID, TERNARY, STR, VAL, LEN, UPPER, LOWER,
                     ROUND, MAX, MIN, INSTR, PI, RNDINT, TAB, LEFT, RIGHT}

        def __init__(self, column, category, lexeme):

            self.column = column      # Column in which token starts
            self.category = category  # Category of the token
            self.lexeme = lexeme      # Token in string form

        def pretty_print(self):
            """Pretty prints the token

            """
            print('Column:', self.column,
                  'Category:', self.catnames[self.category],
                  'Lexeme:', self.lexeme)

        def print_lexeme(self):
            print(self.lexeme, end=' ')

class Lexer:

    def __init__(self):

        self.__column = 0  # Current column number
        self.__stmt = ''   # Statement string being processed

    def tokenize(self, stmt):
        """Returns a list of tokens obtained by
        lexical analysis of the specified
        statement.

        """
        self.__stmt = stmt
        self.__column = 0

        # Establish a list of tokens to be
        # derived from the statement
        tokenlist = []

        # Process every character until we
        # reach the end of the statement string
        c = self.__get_next_char()
        while c != '':

            # Skip any preceding whitespace
            while c.isspace():
                c = self.__get_next_char()

            # Construct a token, column count already
            # incremented
            token = Token(self.__column - 1, None, '')

            # Process strings
            if c == '"':
                token.category = Token.STRING

                # Consume all of the characters
                # until we reach the terminating
                # quote. Do not store the quotes
                # in the lexeme
                c = self.__get_next_char()  # Advance past opening quote

                # We explicitly support empty strings
                if c == '"':
                    # String is empty, leave lexeme as ''
                    # and advance past terminating quote
                    c = self.__get_next_char()

                else:
                    while True:
                        token.lexeme += c  # Append the current char to the lexeme
                        c = self.__get_next_char()

                        if c == '':
                            raise SyntaxError("Mismatched quotes")

                        if c == '"':
                            c = self.__get_next_char()  # Advance past terminating quote
                            break

            # Process numbers
            elif c.isdigit():
                token.category = Token.UNSIGNEDINT
                found_point = False

                # Consume all of the digits, including any decimal point
                while True:
                    token.lexeme += c  # Append the current char to the lexeme
                    c = self.__get_next_char()

                    # Break if next character is not a digit
                    # and this is not the first decimal point
                    if not c.isdigit():
                        if c == '.':
                            if not found_point:
                                found_point = True
                                token.category = Token.UNSIGNEDFLOAT

                            else:
                                # Another decimal point found
                                break

                        else:
                            break

            # Process keywords and names
            elif c.isalpha():
                # Consume all of the letters
                while True:
                    token.lexeme += c  # append the current char to the lexeme
                    c = self.__get_next_char()

                    # Break if not a letter or a dollar symbol
                    # (the latter is used for string variable names)
                    if not ((c.isalpha() or c.isdigit()) or c == '_' or c == '$'):
                        break

                # Normalise keywords and names to upper case
                token.lexeme = token.lexeme.upper()

                # Determine if the lexeme is a variable name or a
                # reserved word
                if token.lexeme in Token.keywords:
                    token.category = Token.keywords[token.lexeme]

                else:
                    token.category = Token.NAME

                # Remark Statements - process rest of statement without checks
                if token.lexeme == "REM":
                    while c!= '':
                        token.lexeme += c  # Append the current char to the lexeme
                        c = self.__get_next_char()

            # Process operator symbols
            elif c in Token.smalltokens:
                save = c
                c = self.__get_next_char()  # c might be '' (end of stmt)
                twochar = save + c

                if twochar in Token.smalltokens:
                    token.category = Token.smalltokens[twochar]
                    token.lexeme = twochar
                    c = self.__get_next_char() # Move past end of token

                else:
                    # One char token
                    token.category = Token.smalltokens[save]
                    token.lexeme = save

            # We do not recognise this token
            elif c != '':
                raise SyntaxError('Syntax error')

            # Append the new token to the list
            tokenlist.append(token)

        return tokenlist

    def __get_next_char(self):
        """Returns the next character in the
        statement, unless the last character has already
        been processed, in which case, the empty string is
        returned.

        """
        if self.__column < len(self.__stmt):
            next_char = self.__stmt[self.__column]
            self.__column = self.__column + 1

            return next_char

        else:
            return ''


if __name__ == "__main__":
    import doctest
    doctest.testmod()

def main():
    lexer = Lexer()
    program = Program()

    # Continuously accept user input and act on it until
    # the user enters 'EXIT'
    while True:

        stmt = str(input('[ BETTERCMD BASIC ] >>> '))

        # stmtlist = list(stmt)
        # stmtout = ''
        # if not stmtlist[0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
        #     stmtout = f'10 {stmt}'
        #     stmt = stmtout

        try:
            tokenlist = lexer.tokenize(stmt)

            # Execute commands directly, otherwise
            # add program statements to the stored
            # BASIC program

            if len(tokenlist) > 0:

                # Exit the interpreter
                if tokenlist[0].category == Token.EXIT:
                    break

                # Add a new program statement, beginning
                # a line number
                elif tokenlist[0].category == Token.UNSIGNEDINT\
                     and len(tokenlist) > 1:
                    program.add_stmt(tokenlist)

                # Delete a statement from the program
                elif tokenlist[0].category == Token.UNSIGNEDINT \
                        and len(tokenlist) == 1:
                    program.delete_statement(int(tokenlist[0].lexeme))

                # Execute the program
                elif tokenlist[0].category == Token.RUN:
                    try:
                        program.execute()

                    except KeyboardInterrupt:
                        print("Program terminated")

                # List the program
                elif tokenlist[0].category == Token.LIST:
                     if len(tokenlist) == 2:
                         program.list(int(tokenlist[1].lexeme),int(tokenlist[1].lexeme))
                     elif len(tokenlist) == 3:
                         # if we have 3 tokens, it might be LIST x y for a range
                         # or LIST -y or list x- for a start to y, or x to end
                         if tokenlist[1].lexeme == "-":
                             program.list(None, int(tokenlist[2].lexeme))
                         elif tokenlist[2].lexeme == "-":
                             program.list(int(tokenlist[1].lexeme), None)
                         else:
                             program.list(int(tokenlist[1].lexeme),int(tokenlist[2].lexeme))
                     elif len(tokenlist) == 4:
                         # if we have 4, assume LIST x-y or some other
                         # delimiter for a range
                         program.list(int(tokenlist[1].lexeme),int(tokenlist[3].lexeme))
                     else:
                         program.list()

                # Save the program to disk
                elif tokenlist[0].category == Token.SAVE:
                    program.save(tokenlist[1].lexeme)
                    print("Program written to file")

                # Load the program from disk
                elif tokenlist[0].category == Token.LOAD:
                    program.load(tokenlist[1].lexeme)
                    print("Program read from file")

                # Delete the program from memory
                elif tokenlist[0].category == Token.NEW:
                    program.delete()

                # Unrecognised input
                else:
                    print("Unrecognised input", file=stderr)
                    for token in tokenlist:
                        token.print_lexeme()
                    print(flush=True)

        # Trap all exceptions so that interpreter
        # keeps running
        except Exception as e:
            print(e, file=stderr, flush=True)


if __name__ == "__main__":
    main()
