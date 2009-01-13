/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTUtils;
import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class IfStatement extends Statement implements XMLGenerator {
	public enum Type {
		IF,
		IFTHEN,
		ELSE, 
		ELSEIFTHEN
	}
	
	private Type type;
	private Expression condition;
	private List<Statement> statements;
	
	public IfStatement(Type type) {
		super();
		this.type = type;
	}
	public List<Statement> getStatements() {
		return statements;
	}
	public void setStatements(List<Statement> statements) {
		this.statements = statements;
	}
	public void setAction(Statement action) {
		this.statements = new ArrayList<Statement>();
		this.statements.add(action);
	}
	public Expression getCondition() {
		return condition;
	}
	public void setCondition(Expression condition) {
		this.condition = condition;
	}
	@Override
	public String toString() {
		if(type==Type.IF)
			return "if("+condition+") ";
		else if(type==Type.IFTHEN)
			return "if("+condition+") then";
		else if(type==Type.ELSE) 
			return "else";
		else if(type==Type.ELSEIFTHEN)
			return "elseif("+condition+") then";
		
		return super.toString();
	}
	public Type getType() {
		return type;
	}
	public void setType(Type type) {
		this.type = type;
	}
	
	public Object astWalk(ASTVisitor visitor) {
		if(condition!=null) {
			condition.astWalk(visitor);
		}
		if(statements!=null)
		for(Statement statement: statements) {
			statement.astWalk(visitor);
		}
		
		return visitor.visit(this);		
	}
	
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", type.name().toLowerCase());
		handler.startElement("", "", "statement", attrs);
		
		super.generateXML(handler);
		
		if(condition instanceof XMLGenerator) {
			handler.startElement("", "", "condition", null);
			((XMLGenerator)condition).generateXML(handler);
			handler.endElement("", "", "condition");
		}
				
		if(statements!=null) {
			handler.startElement("", "", "block", null);
			Location location = ASTUtils.calculateBlockLocation(getStatements());
			if(location!=null)
				location.generateXML(handler);			
			for(Statement statement: statements) {
				if(statement instanceof XMLGenerator)
					((XMLGenerator)statement).generateXML(handler);
			}
			handler.endElement("", "", "block");
		}
		
		handler.endElement("", "", "statement");
	}
}
