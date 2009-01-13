/**
 * 
 */
package ee.olegus.fortran.ast;

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
public class PrintStatement extends Statement implements XMLGenerator {
	private Expression format;
	private List<Expression> outputs;

	public List<Expression> getOutputs() {
		return outputs;
	}

	public void setOutputs(List<Expression> outputs) {
		this.outputs = outputs;
	}

	public Expression getFormat() {
		return format;
	}

	public void setFormat(Expression format) {
		this.format = format;
	}

	public Object astWalk(ASTVisitor visitor) {
		for(Expression output: outputs) {
			output.astWalk(visitor);
		}
		
		return visitor.visit(this);
	}


	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "print");
		handler.startElement("", "", "statement", attrs);
		
		super.generateXML(handler);

		if (format!=null) {
			handler.startElement("", "", "format", null);
			format.generateXML(handler);
			handler.endElement("", "", "format");
		}
		
		if (outputs!=null && outputs.size()>0) {
			handler.startElement("", "", "values", null);
			for(int i=0; i<outputs.size(); i++) {
				outputs.get(i).generateXML(handler);
			}
			handler.endElement("", "", "values");
		}
		
		handler.endElement("", "", "statement");
	}	
}
