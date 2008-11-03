/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;

/**
 * @author olegus
 *
 */
public class SelectCaseStatement extends Statement  implements XMLGenerator {
	private Expression expression;
	private List<CaseStatement> caseStatements = new ArrayList<CaseStatement>();
	
	public List<CaseStatement> getCaseStatements() {
		return caseStatements;
	}
	public void setCaseStatements(List<CaseStatement> caseStatements) {
		this.caseStatements = caseStatements;
	}
	public Expression getExpression() {
		return expression;
	}
	public void setExpression(Expression expression) {
		this.expression = expression;
	}
	public Object astWalk(ASTVisitor visitor) {
		expression.astWalk(visitor);
		
		if(caseStatements!=null)
		for(CaseStatement stmt: caseStatements) {
			stmt.astWalk(visitor);
		}
		
		return visitor.visit(this);		
	}
	
	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "selectcase");
		handler.startElement("", "", "statement", attrs);
		
		super.generateXML(handler);
		handler.startElement("", "", "value", null);
		expression.generateXML(handler);
		handler.endElement("", "", "value");
		
		for(CaseStatement caseStatement: caseStatements) {
			caseStatement.generateXML(handler);
		}
		
		handler.endElement("", "", "statement");
	}
}
