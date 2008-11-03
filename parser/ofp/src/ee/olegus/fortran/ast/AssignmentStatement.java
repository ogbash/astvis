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
public class AssignmentStatement extends Statement implements XMLGenerator {
	
	public enum Type {
		ASSIGNMENT,
		POINTER_ASSIGNMENT
	}
	
	private Type type;
	private DataReference target;
	private Expression expression;
	
	public AssignmentStatement() {
		this(Type.ASSIGNMENT);
	}
	
	public AssignmentStatement(Type type) {
		this.type = type;
	}
	
	public Expression getExpression() {
		return expression;
	}
	public void setExpression(Expression expression) {
		this.expression = expression;
	}
	public DataReference getTarget() {
		return target;
	}
	public void setTarget(DataReference target) {
		this.target = target;
	}

	public Type getType() {
		return type;
	}

	public void setType(Type type) {
		this.type = type;
	}

	@Override
	public String toString() {
		return target
			+ (type==Type.ASSIGNMENT?"=":"=>")
			+ expression;
	}

	public Object astWalk(ASTVisitor visitor) {
		expression = (Expression) expression.astWalk(visitor);
		return visitor.visit(this);
	}
	
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "assignment");
		handler.startElement("", "", "statement", attrs);
		
		super.generateXML(handler);
		
		if(target instanceof XMLGenerator) {
			handler.startElement("", "", "target", null);
			((XMLGenerator)target).generateXML(handler);
			handler.endElement("", "", "target");
		}
		if(expression instanceof XMLGenerator) {
			handler.startElement("", "", "value", null);
			((XMLGenerator)expression).generateXML(handler);
			handler.endElement("", "", "value");
		}
		handler.endElement("", "", "statement");
	}	
}
