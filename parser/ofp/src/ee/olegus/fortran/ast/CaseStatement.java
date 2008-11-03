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
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class CaseStatement extends Statement {
	/**
	 * List of value ranges for the case.
	 */
	private List<Expression[]> selector;
	private List<Statement> block = new ArrayList<Statement>();
	
	public List<Statement> getBlock() {
		return block;
	}
	public void setBlock(List<Statement> block) {
		this.block = block;
	}
	public List<Expression[]> getSelector() {
		return selector;
	}
	public void setSelector(List<Expression[]> selector) {
		this.selector = selector;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		handler.startElement("", "", "case", null);
		super.generateXML(handler);
		
		if(selector!=null) {
			handler.startElement("", "", "selector", null);
			for(int i=0; i<selector.size(); i++) {
				if(selector.get(i)[1]==null) { // subscript
					handler.startElement("", "", "subscript", null);
					selector.get(i)[0].generateXML(handler);
					handler.endElement("", "", "subscript");
					
				} else { // range
					handler.startElement("", "", "section", null);
					if(selector.get(i)[0] instanceof Expression) {
						handler.startElement("", "", "start", null);
						selector.get(i)[0].generateXML(handler);
						handler.endElement("", "", "start");
					}
					if(selector.get(i)[1] instanceof Expression) {
						handler.startElement("", "", "stop", null);
						selector.get(i)[1].generateXML(handler);
						handler.endElement("", "", "stop");
					}
					handler.endElement("", "", "section");
				}
			}
				
			handler.endElement("", "", "selector");
		}
		
		// block
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "executions");
		handler.startElement("", "", "block", attrs);

		Location location = ASTUtils.calculateBlockLocation(getBlock());
		if(location!=null)
			location.generateXML(handler);
		
		for(Statement statement: block) {
			statement.generateXML(handler);
		}
		handler.endElement("", "", "block");

		handler.endElement("", "", "case");
	}
}
