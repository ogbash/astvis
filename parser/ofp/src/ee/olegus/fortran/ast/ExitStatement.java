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
public class ExitStatement extends Statement implements XMLGenerator {
	
	private String exitId;

	public String getKeyword() {
		return exitId;
	}

	public void setKeyword(String keyword) {
		this.exitId = keyword;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
		
	}

	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		if (exitId!=null)
			attrs.addAttribute ("", "", "exitId", "", exitId);
		handler.startElement("", "", "exit", attrs);
		super.generateXML(handler);
		handler.endElement("", "", "exit");
	}
}
