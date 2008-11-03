/**
 * 
 */
package ee.olegus.fortran.parser;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.antlr.runtime.Token;
import org.antlr.runtime.TokenStream;

import fortran.ofp.parser.java.FortranParser;
import fortran.ofp.parser.java.IActionEnums;
import ee.olegus.fortran.ast.ActualArgument;
import ee.olegus.fortran.ast.ArraySpecificationElement;
import ee.olegus.fortran.ast.Attribute;
import ee.olegus.fortran.ast.DoStatement;
import ee.olegus.fortran.ast.Expression;
import ee.olegus.fortran.ast.OperatorExpression;
import ee.olegus.fortran.ast.Statement;
import ee.olegus.fortran.ast.Subprogram;
import ee.olegus.fortran.ast.Attribute.IntentType;

/**
 * @author olegus
 *
 */
public class ParserActionUtils {
	
	static Map<Integer,OperatorExpression.Operator> operatorMap = 
		new HashMap<Integer, OperatorExpression.Operator>();
	
	static {
		operatorMap.put(FortranParser.T_PLUS, OperatorExpression.Operator.ADD);
		operatorMap.put(FortranParser.T_MINUS, OperatorExpression.Operator.SUB);
		operatorMap.put(FortranParser.T_ASTERISK, OperatorExpression.Operator.MUL);
		operatorMap.put(FortranParser.T_SLASH, OperatorExpression.Operator.DIV);
		operatorMap.put(FortranParser.T_POWER, OperatorExpression.Operator.POW);
		operatorMap.put(FortranParser.T_LESSTHAN, OperatorExpression.Operator.LESS);
		operatorMap.put(FortranParser.T_LESSTHAN_EQ, OperatorExpression.Operator.LESS_EQUAL);
		operatorMap.put(FortranParser.T_GREATERTHAN, OperatorExpression.Operator.GREATER);
		operatorMap.put(FortranParser.T_GREATERTHAN_EQ, OperatorExpression.Operator.GREATER_EQUAL);
		operatorMap.put(FortranParser.T_EQ_EQ, OperatorExpression.Operator.EQUAL);
		operatorMap.put(FortranParser.T_NE, OperatorExpression.Operator.NOT_EQUAL);

		operatorMap.put(FortranParser.T_NOT, OperatorExpression.Operator.NOT);
		operatorMap.put(FortranParser.T_AND, OperatorExpression.Operator.AND);
		operatorMap.put(FortranParser.T_OR, OperatorExpression.Operator.OR);
		operatorMap.put(FortranParser.T_EQ, OperatorExpression.Operator.EQ);
		operatorMap.put(FortranParser.T_EQV, OperatorExpression.Operator.EQV);
		operatorMap.put(FortranParser.T_NEQV, OperatorExpression.Operator.NEQV);		
	}
	
	private FortranParser parser;
	
	ParserActionUtils(FortranParser parser) {
		this.parser = parser;
	}
	
	/**
	 * Creates expression AST from parse stack elements and puts it back on the stack.
	 * @param parseStack
	 * @param numOps
	 */
	void collapseOperand(ParserStack<Object> parseStack, int numOps) {
		// touch stack only if operators exist
		if(numOps>0) {
			try {
			Object[] list = new Object[numOps*2+1];
			for(int i=list.length-1; i>=0; i--)
				list[i] = parseStack.pop();

			Expression left = (Expression) list[0];
			for(int i=0; i<numOps; i++) {
				Token opToken = (Token) list[i*2+2];
				OperatorExpression.Operator op = operatorMap.get(opToken.getType());
				OperatorExpression expr = new OperatorExpression(op);
				Expression right = (Expression) list[i*2+1];
				expr.setLeftExpression(left);
				expr.setRightExpression(right);
				left = expr;
			}
		
			parseStack.push(left);
			}catch (RuntimeException e) {
				System.err.println("numOps="+numOps);
				System.err.println(parser.getTokenStream().LT(1));
				throw e;
			}

		}		
	}

	
	/**
	 * @param subscripts
	 */
	public boolean isArgumentList(List<Object> subscripts) {
		boolean areArguments = false;
		for(Iterator<Object> iter=subscripts.iterator(); iter.hasNext(); ) {
			Object object = iter.next();
			if(object instanceof ActualArgument)
				areArguments = true;			
		}
		
		return areArguments; 
	}	
	
	
	/**
	 * Helper method, because of several different type specification parse methods (eg usual and component).
	 * @param parserStack
	 * @param attrNum
	 * @return
	 */
	@SuppressWarnings("unchecked")
	Attribute parseAttribute(ParserStack<Object> parseStack, int attrNum) {
		Attribute attribute;
		
		try {
		
		switch (attrNum) {
		case IActionEnums.AttrSpec_DIMENSION:
		case IActionEnums.ComponentAttrSpec_dimension_paren:
			attribute = new Attribute(Attribute.Type.DIMENSION);
			attribute.setArraySpecification((List<ArraySpecificationElement>) parseStack.pop());
			break;
		case IActionEnums.AttrSpec_PARAMETER:
			attribute = new Attribute(Attribute.Type.PARAMETER);
			break;
		case IActionEnums.AttrSpec_OPTIONAL:
			attribute = new Attribute(Attribute.Type.OPTIONAL);
			break;
		case IActionEnums.AttrSpec_INTENT:
			attribute = new Attribute(Attribute.Type.INTENT);
			attribute.setIntent((IntentType) parseStack.pop());
			break;
		case IActionEnums.AttrSpec_POINTER:
		case IActionEnums.ComponentAttrSpec_pointer:
			attribute = new Attribute(Attribute.Type.POINTER);
			break;
		case IActionEnums.AttrSpec_TARGET:
			attribute = new Attribute(Attribute.Type.TARGET);
			break;
		case IActionEnums.AttrSpec_SAVE:
			attribute = new Attribute(Attribute.Type.SAVE);
			break;
		case IActionEnums.AttrSpec_access:
			attribute = new Attribute((Attribute.Type) parseStack.pop());
			break;
		case IActionEnums.AttrSpec_ALLOCATABLE:
			attribute = new Attribute(Attribute.Type.ALLOCATABLE);
			break;		
		default:
			System.err.println("Parser incomplete: attr_spec at " + parser.getTokenStream().LT(1));
			return null;
		}
		
		return attribute;

		}catch (RuntimeException e) {
			System.err.println(parser.getTokenStream().LT(1));
			throw e;
		}
		
	}

	/**
	 * @param type
	 * @return
	 */
	public OperatorExpression.Operator findOperator(int type) {
		return operatorMap.get(type);
	}
	
	/**
	 * @param parseStack
	 * @return
	 */
	public List<Statement> collectStatements(ParserStack<Object> parseStack) {
		List<Statement> stmts = new ArrayList<Statement>();
		
		
		int start = parseStack.peekMark();
		while(parseStack.size() > start) {
			Object obj = parseStack.pop();
			if(obj instanceof Statement) {
				stmts.add(0, (Statement) obj);
			} else {
				System.err.println("Not statement: "+obj);
			}
		}		
		
		return stmts;
	}

	/**
	 * @param parseStack
	 * @return
	 */
	public List<Subprogram> collectSubprograms(ParserStack<Object> parseStack) {
		List<Subprogram> subs = new ArrayList<Subprogram>();
		
		int start = parseStack.peekMark();
		while(parseStack.size() > start && parseStack.peek() instanceof Subprogram) {
			Subprogram sub = (Subprogram) parseStack.pop();
			subs.add(0, sub);
		}		
		
		return subs;
	}

	/**
	 * Check if given label is the innermost loop label and collapse it if necessary.
	 * 
	 * @param label
	 * @param parseStack
	 */
	public void collapseLoopsOnLabel(Token label, ParserStack<Object> parseStack) {
		if(parseStack.markCount() == 0)
			return;
		
		int index = parseStack.peekMark();
		Object obj = parseStack.get(index-1);
		
		if(obj instanceof DoStatement) {
			DoStatement stmt = (DoStatement) obj;
			if(label.getText().equals(stmt.getDoLabel())) {
				// collapse
				List<Statement> statements = collectStatements(parseStack);
				parseStack.popMark();
				stmt.setStatements(statements);
			}
		}
	}
	
	int findReverseToken(Token token, TokenStream tokenStream) {
		int i=tokenStream.index();
		while(i>=0) {
			if(tokenStream.get(i) == token)
				break;
			i--;
		}
		
		return i;
	}

	int findReverseToken(int token, TokenStream tokenStream) {
		int i=tokenStream.index()-1;
		while(i>=0) {
			if(tokenStream.get(i).getType() == token)
				break;
			i--;
		}
		
		return i;
	}

	int findReverseToken(TokenStream tokenStream) {
		return findReverseToken(tokenStream, tokenStream.index());
	}	
	
	/**
	 * Find in reverse token which is not whitespace nor comment.
	 * @param tokenStream
	 * @return
	 */
	int findReverseToken(TokenStream tokenStream, int end) {
		int i=end-1;
		while(i>=0) {
			Token token = tokenStream.get(i);
			if(token.getChannel() != Token.HIDDEN_CHANNEL &&
					token.getType() != FortranParser.T_EOS)
				break;
			i--;
		}
		
		if(tokenStream.get(i).getLine()==0)
			System.err.println("==="+tokenStream.get(i).getType());
		
		return i;
	}

}
