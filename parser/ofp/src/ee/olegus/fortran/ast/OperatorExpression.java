/**
 * 
 */
package ee.olegus.fortran.ast;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;

/**
 * @author olegus
 *
 */
public class OperatorExpression extends Expression implements XMLGenerator {
	
	public enum Operator {
		CONCAT ("//"),
		ADD ("+"),
		SUB ("-"),
		MUL ("*"),
		DIV ("/"),
		POW ("**"),
		LESS ("<"),
		LESS_EQUAL ("<="),
		GREATER (">"),
		GREATER_EQUAL (">="),
		EQUAL ("=="),
		NOT_EQUAL ("/="),
		
		NOT (".NOT."),
		AND (".AND."),
		OR (".OR."),
		EQV (".EQV."),
		NEQV (".NEQV"), 
		EQ (".EQ.");
		
		private String string;
		Operator(String symbol) {
			this.string = symbol;
		}
		
		String getString() {return string;}
	};
	
	private Operator operator;
	private Expression leftExpression, rightExpression;
	
	public OperatorExpression(Operator operator) {
		this.operator = operator;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getDimensions()
	 */
	public int getDimensions() {
		// TODO Auto-generated method stub
		return 0;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getType()
	 */
	public Type getType() {
		// TODO Auto-generated method stub
		return null;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#hasAttribute(ee.olegus.fortran.ast.Attribute.Type)
	 */
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		// TODO Auto-generated method stub
		return false;
	}

	public Expression getLeftExpression() {
		return leftExpression;
	}

	public void setLeftExpression(Expression leftExpression) {
		this.leftExpression = leftExpression;
	}

	public Operator getOperator() {
		return operator;
	}

	public void setOperator(Operator operator) {
		this.operator = operator;
	}

	public Expression getRightExpression() {
		return rightExpression;
	}

	public void setRightExpression(Expression rightExpression) {
		this.rightExpression = rightExpression;
	}

	@Override
	public String toString() {
		return "("+leftExpression + (operator!=null?operator.string:"?op?") + rightExpression+")";
	}

	public Object astWalk(ASTVisitor visitor) {
		if(leftExpression != null) {
			leftExpression = (Expression) leftExpression.astWalk(visitor);
		}
		if(rightExpression != null) {
			rightExpression = (Expression) rightExpression.astWalk(visitor);
		}
		
		return visitor.visit(this);
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		if(operator!=null)
			attrs.addAttribute("", "", "type", "", operator.string);
		handler.startElement("", "", "operator", attrs);
		if(leftExpression instanceof XMLGenerator) {
			handler.startElement("", "", "left", null);
			((XMLGenerator)leftExpression).generateXML(handler);
			handler.endElement("", "", "left");
		}
		if(rightExpression instanceof XMLGenerator) {
			handler.startElement("", "", "right", null);
			((XMLGenerator)rightExpression).generateXML(handler);
			handler.endElement("", "", "right");
		}
		handler.endElement("", "", "operator");
	}
}
