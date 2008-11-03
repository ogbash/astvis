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
public class Constant extends Expression implements XMLGenerator {
	
	public enum Type {
		INTEGER,
		REAL,
		STRING,
		LOGICAL,
		CHARACTER,
		NULL, /* NULL() */
		COMPLEX
	}
	
	private Type constantType;
	private String value;
	private String kind;

	public String getKind() {
		return kind;
	}

	public void setKind(String kind) {
		this.kind = kind;
	}

	public String getValue() {
		return value;
	}

	public void setValue(String value) {
		this.value = value;
	}

	public Constant(Type type) {
		this.constantType = type;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getDimensions()
	 */
	public int getDimensions() {
		// TODO Auto-generated method stub
		return 0;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getType()
	 */
	public Type getConstantType() {
		return constantType;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#hasAttribute(ee.olegus.fortran.ast.Attribute.Type)
	 */
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		// TODO Auto-generated method stub
		return false;
	}

	public ee.olegus.fortran.ast.Type getType() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public String toString() {
		return "Constant<"+constantType+">("+value+")";
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", constantType.name().toLowerCase());
		if (kind!=null)
			attrs.addAttribute("", "", "kind", "", kind);
		handler.startElement("", "", "constant", attrs);
		if(value!=null)
			handler.characters(value.toCharArray(), 0, value.length());
		handler.endElement("", "", "constant");
	}
}
