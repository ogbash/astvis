/**
 * 
 */
package ee.olegus.fortran.ast;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import ee.olegus.fortran.ASTVisitable;
import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;

/**
 * @author olegus
 *
 */
public class Subscript implements ASTVisitable, XMLGenerator {
	protected Expression expression;

	public Subscript() {}
	
	public Subscript(Expression expression) {
		this.expression = expression;
	}

	public Expression getExpression() {
		return expression;
	}

	public void setExpression(Expression expression) {
		this.expression = expression;
	}

	@Override
	public String toString() {
		return expression!=null ? expression.toString() : "<null>";
	}

	public Object astWalk(ASTVisitor visitor) {
		if(expression!=null)
		expression = (Expression) expression.astWalk(visitor);
		//visitor.visit(this);
		return this;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		handler.startElement("", "", "subscript", null);			
		if(expression instanceof XMLGenerator) {
			((XMLGenerator)expression).generateXML(handler);
		}
		handler.endElement("", "", "subscript");
	}
}
