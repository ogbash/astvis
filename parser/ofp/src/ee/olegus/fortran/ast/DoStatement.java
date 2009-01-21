/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTUtils;
import ee.olegus.fortran.ASTVisitable;
import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class DoStatement extends Statement implements XMLGenerator {
	public enum Type {
		FOR,
		WHILE, 
		NONE
	}
	
	private Type type;
	private DataReference variable;
	private Expression first;
	private Expression last;
	private Expression step;
	private Expression condition;
	private String doLabel;
	
	private List<Statement> statements;

	public DoStatement(Type type) {
		super();
		this.type = type;
	}

	public Expression getFirst() {
		return first;
	}

	public void setFirst(Expression first) {
		this.first = first;
	}

	public Expression getLast() {
		return last;
	}

	public void setLast(Expression last) {
		this.last = last;
	}

	public List<Statement> getStatements() {
		return statements;
	}

	public void setStatements(List<Statement> statements) {
		this.statements = statements;
	}

	public Expression getStep() {
		return step;
	}

	public void setStep(Expression step) {
		this.step = step;
	}

	public Type getType() {
		return type;
	}

	public void setType(Type type) {
		this.type = type;
	}

	public Expression getCondition() {
		return condition;
	}

	public void setCondition(Expression condition) {
		this.condition = condition;
	}

	public DataReference getVariable() {
		return variable;
	}

	public void setVariable(DataReference variable) {
		this.variable = variable;
	}

	@Override
	public String toString() {
		if(type==Type.WHILE) { // while
			return "DO"+(doLabel!=null?" "+doLabel+" ":" ")+"WHILE (" + first + ")";
		} else if(type==Type.FOR) { // for
			return "DO"+(doLabel!=null?" "+doLabel+" ":" ")+variable+"="
				+first+","+last+(step!=null?","+step:"");
		} else {
			return "DO"+(doLabel!=null?" "+doLabel+" ":" ");
		}
	}

	public String getDoLabel() {
		return doLabel;
	}

	public void setDoLabel(String label) {
		this.doLabel = label;
	}

	public Object astWalk(ASTVisitor visitor) {
		if(first instanceof ASTVisitable)
			first = (Expression) first.astWalk(visitor);
		if(last instanceof ASTVisitable)
			last = (Expression) last.astWalk(visitor);
		if(step instanceof ASTVisitable)
			step = (Expression) step.astWalk(visitor);
		
		for(Statement statement: statements) {
			statement.astWalk(visitor);
		}
		
		return visitor.visit(this);
	}
	
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", type.name());
		if(variable!=null)
			attrs.addAttribute("", "", "variable", "", variable.getId().getName());
		handler.startElement("", "", "do", attrs);

		super.generateXML(handler);
		
		if(first instanceof XMLGenerator) {
			handler.startElement("", "", "first", null);
			((XMLGenerator)first).generateXML(handler);
			handler.endElement("", "", "first");
		}
		if(last instanceof XMLGenerator) {
			handler.startElement("", "", "last", null);
			((XMLGenerator)last).generateXML(handler);
			handler.endElement("", "", "last");
		}
		if(step instanceof XMLGenerator) {
			handler.startElement("", "", "step", null);
			((XMLGenerator)step).generateXML(handler);
			handler.endElement("", "", "step");
		}
		if(condition instanceof XMLGenerator) {
			handler.startElement("", "", "condition", null);
			((XMLGenerator)condition).generateXML(handler);
			handler.endElement("", "", "condition");
		}
		
		if(statements!=null) {
			handler.startElement("", "", "block", null);	
			Location loc = ASTUtils.calculateBlockLocation(statements);
			if(loc!=null)
				loc.generateXML(handler);			
			for(Statement statement: statements) {
				if(statement instanceof XMLGenerator)
					((XMLGenerator)statement).generateXML(handler);
			}
			handler.endElement("", "", "block");			
		}
		
		handler.endElement("", "", "do");
	}	
}
