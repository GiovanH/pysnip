"""Interactive user prompts as an interface.
"""
# Wishlist:
# regex matching
import textwrap

def _yes(*args):
    return True


def _echo(s):
    return s


class BasePrompt():
    """A prompt with no builtin commands.
    
    Attributes:
        aliases (dict): alias (str): command (Command)
        commands (dict): name (str): command (Command)
        pstr (str): The prompt string (i.e. '$ ')
    """

    def __init__(self, pstr="> "):
        """Initialize a runnable prompt
        
        Args:
            pstr (str) Override the prompt string (i.e. '$ ')
        """
        self.pstr = pstr
        self.commands = {}
        self.aliases = {}
        self.custom_psession = None
        self.override = None
        self.registerCommandsFromNamespace(self, "cmd_")
        # self.registerCommand("help", self.cmd_help, ["?"], "Print help")
        # self.registerCommand("exit", self.cmd_exit, [
        #                      "quit"], "Exit the prompt")

    def registerCommand(self, name, callback, aliases=[], helpstr=None):
        """Register a command.
        This just wraps the creation of a Command object and registers it.
        
        Args:
            name (string): The name of the function, and the command the users types.
            callback (func):
                The callback function that running this command triggers. 
                Should have signature func(*args)
            aliases (list, optional): List of alias strings
            helpstr (None, optional): 
                Multiline string of help information.
                The first line is automatically used as the short help string.
        """
        self.registerCommandObj(Command(name, callback, aliases, helpstr))

    def registerCommandObj(self, command):
        """Add a command object directly.
        
        Args:
            command (Command)
        """
        name = command.name
        self.commands[name] = command
        for a in command.aliases:
            self.aliases[a] = self.commands[name]

    def registerCommandsFromNamespace(self, namespace, prefix="cmd_"):
        """Searches a namespace for callables with a name
        that matches the pattern "cmd_xxxx" and registers them
        with the name "xxxx" and the function's docstring.
        
        Args:
            namespace
            prefix (str, optional): A substitution for the "cmd_" prefix
        """
        self.registerCommandsFromFuncs(
            [namespace.__getattribute__(name) for name in dir(namespace)],
            matches=(lambda func: func.__name__[0:len(prefix)] == prefix),
            mutilate=(lambda name: name[len(prefix):])
        )

    def registerCommandsFromFuncs(self, funcs, matches=_yes, mutilate=_echo):
        """Registers each callable in funcs that matches the function `matches`.
        Names them based on multilate.
        See chain starting at registerCommandsFromNamespace.
        
        Args:
            funcs (list): List containing callables. Can contain non-callables.
            matches (func): Should return True when function is good.
            mutilate (func): How to alter the function's name.
        """
        for f in funcs:
            try:
                if callable(f) and (f is not self) and matches(f):
                    self.registerCommandFromFunc(f, mutilate)
            except Exception as e:
                print("Cannot register", f, "as function")

    def registerCommandFromFunc(self, func, mutilate=_echo):
        """Register command from existing function.
        See chain starting at registerCommandsFromNamespace.

        Args:
            func (callable): Callable with signature f(*args)
            mutilate (func): How to change the function name
        """
        self.registerCommand(
            mutilate(func.__name__),
            func,
            helpstr=textwrap.dedent(func.__doc__) if func.__doc__ else func.__name__
        )

    def run(self):
        """Run the prompt until user termination.
        Prompt exits on KeyboardInterrupt or EOF.
        """
        from prompt_toolkit import PromptSession
        from prompt_toolkit.patch_stdout import patch_stdout
        from prompt_toolkit.completion import WordCompleter

        prompt_completer = WordCompleter(self.commands.keys())
        if self.custom_psession:
            psession = self.custom_psession
        else:
            psession = PromptSession(completer=prompt_completer, reserve_space_for_menu=3)
        try:
            while True:
                with patch_stdout():
                    rawin = psession.prompt(self.pstr)  # prompt(self.pstr)
                    self.handleCommand(rawin)
        except (KeyboardInterrupt, EOFError) as e:
            # Catch Ctrl-C, Ctrl-D, and exit.
            print("User interrupt.")
        finally:
            # Cleanup
            pass

    def handleCommand(self, rawin):
        # Standard command handling
        import shlex
        inp = shlex.split(rawin)
        if not inp:
            return
        name = inp[0]
        match = self.commands.get(name) or self.aliases.get(name)
        if match:
            # Run command, if a command matches
            try:
                match(*inp[1:])
            except Exception as e:
                import traceback
                traceback.print_exc()
        else:
            print("ERROR: No such command " + name)

    def __call__(self):
        """Calls .run()
        """
        return self.run()


class Prompt(BasePrompt):
    """A prompt with builtin "help" and "exit" commands.
    
    Attributes:
        aliases (dict): alias (str): command (Command)
        commands (dict): name (str): command (Command)
        pstr (str): The prompt string (i.e. '$ ')
    """

    def __init__(self, pstr="> "):
        super().__init__(pstr)
        self.registerCommandsFromNamespace(self, "cmd_")

    def cmd_exit(self, *args):
        """Exit the prompt.
        Same as Ctrl+C.
        
        Args:
            *args: Description
        
        Raises:
            KeyboardInterrupt: Description
        """
        raise KeyboardInterrupt

    def cmd_help(self, *args):
        """Get information about commands (try "help help")

        Usage:
            Run with no arguments to get a list
            of all availible commands.
        
            Run with arguments to get detailed
            help about commands.
        
        Args:
            *args: Description
        """

        if len(args) == 0:
            alen = max([len("command")] + [len(k) for k in self.commands.keys()]) + 2
            blen = max([len("alias")] + [len(k) for k in self.aliases.keys()]) + 2

            def printRow(*row):
                """Summary
                
                Args:
                    *row: Description
                """
                print("{0:{alen}}{1:{blen}}{2:<48}".format(
                    *row,
                    alen=alen,
                    blen=blen
                ))

            printRow(
                "command",
                "alias",
                "help"
            )
            print(*["-"] * 32, sep="")
            for ck in self.commands:
                c = self.commands.get(ck)
                printRow(*c.helprow)
        else:
            for query in args:
                ck = self.commands.get(query)
                if ck:
                    print(ck.helpdoc)
                else:
                    print("No such command: '{}'".format(query))


class Command(object):
    """A command object. Contains a function and metadata.
    
    Args:
        name (string): The name of the function, and the command the users types.
        callback (func):
            The callback function that running this command triggers. 
            Should have signature func(*args)
        aliases (list, optional): List of alias strings
        helpstr (None, optional): 
            Multiline string of help information.
            The first line is automatically used as the short help string.
    """

    def __init__(self, name, callback, aliases=[], helpstr=None):
        self.name = name
        self.callback = callback
        self.aliases = aliases
        if helpstr is None:
            helpstr = "Run command {name}".format(**locals())
        self.helpstr = [line for line in helpstr.split("\n") if line != ""][0]
        self.helpdoc = "== " + self.name + " ==\n" + helpstr

    def run(self, *args):
        """Call the bound function.
        
        Args:
            *args: arguments
        """
        self.callback(*args)

    @property
    def helprow(self):
        """
        Returns:
            tuple: Help row
        """
        return (
            self.name,
            ",".join(a for a in self.aliases),
            self.helpstr
        )

    def __call__(self, *args):
        return self.run(*args)


class Interactable():

    """A class which automatically resolves cmd_ functions into a user prompt.
    
    Attributes:
        prefix (str): Command prefix, default is "cmd_"
    """
    
    def __init__(self, prefix="cmd_", start=True):
        """Summary
        
        Args:
            prefix (str, optional): Description
            start (bool, optional): Description
        """
        # super(Interactable, self).__init__()
        self.prefix = prefix
        if start:
            self.prompt()

    def prompt(self):
        """Summary
        """
        p = Prompt()
        p.registerCommandsFromNamespace(self, self.prefix)
        p()


def test():
    """Summary
    """
    def echo(*args):
        """
        A docstring with newlines and
        weird indentation and specs
        
        Args:
            *args: Description
        
        No Longer Returned:
            None
        """
        print(*args)

    p = Prompt()
    p.registerCommand("alongcommandname", echo, [], "Repeat input")
    p.registerCommand("echo", echo, ['print'], "Repeat input")
    p.registerCommandsFromFuncs([echo])

    p()


if __name__ == "__main__":
    test()
