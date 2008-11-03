/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTUtils;
import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Location;

/**
 * Derived or intrinic type definition.
 * 
 * @author olegus
 *
 */
public class Type extends Declaration implements XMLGenerator {
	private boolean intrinsic;
	private String name;
	private List<? extends Declaration> declarations = new ArrayList<Declaration>(3);

	public Type(String name) {
		super();
		this.name = name;
		this.intrinsic = true;
	}
	
	public Type(CommonTree tree, Code code) {
		super(tree, code, null);
		
		String name = tree.getChild(0).getText();
		declarations = Declaration.parseDeclarations(tree, getLocation().code);
		
		this.name = name;
		this.intrinsic = false;
	}
	
	public String getName() {
		return name;
	}

	@Override
	public String toString() {
		return "Type "+name;
	}

	public List<? extends Declaration> getDeclarations() {
		return declarations;
	}


	public boolean isIntrinsic() {
		return intrinsic;
	}

	public void setDeclarations(List<? extends Declaration> declarations) {
		this.declarations = declarations;
	}

	public void setName(String name) {
		this.name = name;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

	@Override
	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "name", "", name);
		handler.startElement("", "", "typedef", attrs);
		super.generateXML(handler);
		
		attrs.clear(); attrs.addAttribute("", "", "type", "", "declarations");
		handler.startElement("", "", "block", attrs);
		Location loc = ASTUtils.calculateBlockLocation(declarations);
		if(loc!=null)
			loc.generateXML(handler);
		for(Declaration declaration: declarations) {
			declaration.generateXML(handler);
		}
		handler.endElement("", "", "block");
		
		handler.endElement("", "", "typedef");
	}
}
