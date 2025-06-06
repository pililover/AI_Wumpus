import itertools

class Sentence:
    def evaluate(self, model):
        """Evaluates the logical sentence."""
        raise Exception("nothing to evaluate")
    
    def formula(self):
        """Returns string formula representing logical sentence."""
        return ""
    
    def symbols(self):
        """Returns a set of all symbols in the logical sentence."""
        return set()
    
    @classmethod
    def validate(cls, sentence):
        if not isinstance(sentence, Sentence):
            raise TypeError("must be a logical sentence")
        
    @classmethod
    def parenthesize(cls, sentence):
        """Parenthesizes an expression if not already parenthesized."""
        def balanced(s):
            """Checks if a string has balanced parentheses."""
            count = 0
            for c in sentence:
                if c == "(":
                    count+=1
                elif c == ")":
                    if count <= 0:
                        return False
                    count -= 1
            return count == 0
        if not len(sentence) or sentence.isalpha() or (
            sentence[0] == "(" and sentence[-1] == ')' and balanced(sentence[1:-1])
        ):
            return sentence
        return f"({sentence})"
    
    def to_cnf(self):
        """Converts the sentence to CNF."""
        raise NotImplementedError
    
    
class Symbol(Sentence):
    def __init__(self, name):
        self.name = name
        
    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name
    
    def __hash__(self):
        return hash(('symbol', self.name))
    
    def __repr__(self):
        return self.name
    
    def evaluate(self, model):
        try:
            return bool(model[self.name])
        except KeyError:
            raise EvaluationException(f'variable {self.name} not in model')
        
    def formula(self):
        return self.name
    
    def symbols(self):
        return {self.name}
    
    def to_cnf(self):
        return self
    
class Not(Sentence):
    def __init__(self, operand):
        Sentence.validate(operand)
        self.operand = operand
        
    def __eq__(self, other):
        return isinstance(other, Not) and self.operand == other.operand
    
    def __hash__(self):
        return hash(('not', hash(self.operand)))
    
    def __repr__(self):
        return f"Not({self.operand})"
    
    def evaluate(self, model):
        return not self.operand.evaluate(model)
    
    def formula(self):
        return chr(0xAC) + Sentence.parenthesize(self.operand.formula())
    
    def symbols(self):
        return self.operand.symbols()
    
    def to_cnf(self):
        if isinstance(self.operand, Not):
            return self.operand.operand.to_cnf()
        elif isinstance(self.operand, And):
            return Or(*(Not(conjunct).to_cnf() for conjunct in self.operand.conjuncts)).to_cnf()
        elif isinstance(self.operand, Or):
            return And(*(Not(disjunct).to_cnf() for disjunct in self.operand.disjuncts)).to_cnf()
        else:
            return Not(self.operand.to_cnf())
    
class And(Sentence):
    def __init__(self, *conjuncts):
        for conjunct in conjuncts:
            Sentence.validate(conjunct)
        self.conjuncts = list(conjuncts)
        
    def __eq__(self, other):
        return isinstance(other, And) and self.conjuncts == other.conjuncts
    
    def __hash__(self):
        return hash(('and', tuple(hash(conjunct) for conjunct in self.conjuncts)))
    
    def __repr__(self):
        conjuncts = ', '.join([str(conjunct) for conjunct in self.conjuncts])
        return f"And({conjuncts})"
    
    def add(self, conjunct):
        Sentence.validate(conjunct)
        self.conjuncts.append(conjunct)
    
    def evaluate(self, model):
        return all(conjunct.evaluate(model) for conjunct in self.conjuncts)
    
    def formula(self):
        if len(self.conjuncts) == 1:
            return self.conjuncts[0].formula()
        return f" {chr(0x2227)} ".join([Sentence.parenthesize(conjunct.formula()) for conjunct in self.conjuncts])
    
    def symbols(self):
        return set.union(*[conjunct.symbols() for conjunct in self.conjuncts])
    
    def to_cnf(self):
        return And(*(conjunct.to_cnf() for conjunct in self.conjuncts))
    
class Or(Sentence):
    def __init__(self, *disjuncts):
        for disjunct in disjuncts:
            Sentence.validate(disjunct)
        self.disjuncts = list(disjuncts)
        
    def __eq__(self, other):
        return isinstance(other, Or) and self.disjuncts == other.disjuncts
    
    def __hash__(self):
        return hash(('or', tuple(hash(disjunct) for disjunct in self.disjuncts)))
    
    def __repr__(self):
        disjuncts = ', '.join([str(disjunct) for disjunct in self.disjuncts])
        return f"Or({disjuncts})"
    
    def evaluate(self, model):
        return any(disjunct.evaluate(model) for disjunct in self.disjuncts)
    
    def formula(self):  
        if len(self.disjuncts) == 1:
            return self.disjuncts[0].formula()
        return f" {chr(0x2228)} ".join([Sentence.parenthesize(disjunct.formula()) for disjunct in self.disjuncts])
    
    def symbols(self):
        return set.union(*[disjunct.symbols() for disjunct in self.disjuncts])
    
    def to_cnf(self):
        if len(self.disjuncts) == 1:
            return self.disjuncts[0].to_cnf()
        new_disjuncts = []
        for disjunct in self.disjuncts:
            new_disjuncts.append(disjunct.to_cnf())
        return self._distribute_or(new_disjuncts)
    
    @staticmethod
    def _distribute_or(disjuncts):
        # Distribution logic
        # Distribute OR over AND to convert to CNF
        if not disjuncts:
            return And()  # Empty And is essentially True
        if len(disjuncts) == 1:
            return disjuncts[0]
        if isinstance(disjuncts[0], And):
            rest_disjunction = Or._distribute_or(disjuncts[1:])
            return And(*[Or(conjunct, rest_disjunction).to_cnf() for conjunct in disjuncts[0].conjuncts])
        if isinstance(disjuncts[1], And):
            return Or._distribute_or([disjuncts[1], disjuncts[0]])
        return Or(*disjuncts)

class Implication(Sentence):
    def __init__(self, antecedent, consequent):
        Sentence.validate(antecedent)
        Sentence.validate(consequent)
        self.antecedent = antecedent
        self.consequent = consequent
        
    def __eq__(self, other):
        return isinstance(other, Implication) and self.antecedent == other.antecedent and self.consequent == other.consequent
    
    def __hash__(self):
        return hash(('implies', hash(self.antecedent), hash(self.consequent)))
    
    def __repr__(self):
        return f"Implication({self.antecedent}, {self.consequent})"
    
    def evaluate(self, model):
        return ((not self.antecedent.evaluate(model)) or self.consequent.evaluate(model))
    
    def formula(self):
        antecedent = Sentence.parenthesize(self.antecedent.formula())
        consequent = Sentence.parenthesize(self.consequent.formula())
        return f"{antecedent} => {consequent}"
    
    def symbols(self):
        return set.union(self.antecedent.symbols(), self.consequent.symbols())
    
    def to_cnf(self):
        return Or(Not(self.antecedent), self.consequent).to_cnf()
    
class Biconditional(Sentence):
    def __init__(self, left, right):
        Sentence.validate(left)
        Sentence.validate(right)
        self.left = left
        self.right = right

    def __eq__(self, other):
        return isinstance(other, Biconditional) and self.left == other.left and self.right == other.right
    
    def __hash__(self):
        return hash(('biconditional', hash(self.left), hash(self.right)))
    
    def __repr__(self):
        return f"Implication({self.left}, {self.right})"
    
    def evaluate(self, model):
        return (self.left.evaluate(model) and self.right.evaluate(model)
                or (not self.left.evaluate(model) and not self.right.evaluate(model)))
    
    def formula(self):
        left = Sentence.parenthesize(self.left.formula())
        right = Sentence.parenthesize(self.right.formula())
        return f"{left} <=> {right}"
    
    def symbols(self):
        return set.union(self.left.symbols(), self.right.symbols()) 
    
    def to_cnf(self):
        left_to_right = Implication(self.left, self.right)
        right_to_left = Implication(self.right, self.left)
        return And(left_to_right.to_cnf(), right_to_left.to_cnf()).to_cnf()