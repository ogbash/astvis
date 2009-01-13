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
public class StopStatement extends Statement implements XMLGenerator {
	private Expression stopCode;

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitable#astWalk(ee.olegus.fortran.ASTVisitor)
	 */
	public Object astWalk(ASTVisitor visitor) {
		return null;
	}

	public Expression getStopCode() {
		return stopCode;
	}

	public void setStopCode(Expression stopCode) {
		this.stopCode = stopCode;
	}

	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "stop");
		handler.startElement("", "", "statement", attrs);
		
		super.generateXML(handler);
		if (stopCode!=null) {
			handler.startElement("", "", "value", null);
			stopCode.generateXML(handler);
			handler.endElement("", "", "value");
		}
		
		handler.endElement("", "", "statement");
	}
}
