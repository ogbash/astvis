package ee.olegus.fortran.ast;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;


/**
 * Subsript or subscript triplet.
 * 
 * @author olegus
 *
 */
public class SectionSubscript extends Subscript {

	private Expression last;
	private Expression stride;
	
	public Expression getFirst() {
		return getExpression();
	}
	public void setFirst(Expression first) {
		setExpression(first);
	}
	public Expression getLast() {
		return last;
	}
	public void setLast(Expression last) {
		this.last = last;
	}
	public Expression getStride() {
		return stride;
	}
	public void setStride(Expression stride) {
		this.stride = stride;
	}
	
	@Override
	public Object astWalk(ASTVisitor visitor) {
		super.astWalk(visitor);
		
		if(last != null) {
			last = (Expression) last.astWalk(visitor);
		}
		if(stride!=null) {
			stride = (Expression) stride.astWalk(visitor);
		}
		
		//visitor.visit(this);
		return this;		
	}
	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		handler.startElement("", "", "section", null);
		
		AttributesImpl attrs = new AttributesImpl();

		if(expression instanceof XMLGenerator) {
			handler.startElement("", "", "first", attrs);			
			((XMLGenerator)expression).generateXML(handler);
			handler.endElement("", "", "first");			
		}

		if(last instanceof XMLGenerator) {
			handler.startElement("", "", "last", attrs);			
			((XMLGenerator)last).generateXML(handler);
			handler.endElement("", "", "last");			
		}

		if(stride instanceof XMLGenerator) {
			handler.startElement("", "", "stride", attrs);			
			((XMLGenerator)stride).generateXML(handler);
			handler.endElement("", "", "stride");			
		}

		handler.endElement("", "", "section");
	}
	
	
	
}
