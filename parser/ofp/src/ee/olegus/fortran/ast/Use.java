package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.antlr.runtime.tree.Tree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;

public class Use extends Statement implements XMLGenerator {
	public Use(String name) {
		this.name = name;
	}

	private String name;

	@Override
	public String toString() {
		return name;
	}
	
	/**
	 * @deprecated use parser action
	 */
	public static List<Use> parseUses(Tree tree) {
		List<Use> uses = new ArrayList<Use>();
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			Tree child = tree.getChild(i);
			Use use;
			switch(child.getType()) {
			case FortranParser.T_IDENT:
				use = new Use(child.getText());
				uses.add(use);
			}
		}*/
		return uses;
	}

	public String getName() {
		return name;
	}
	
	public String getRenaming(String name) {
		return null; // TODO implement
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "id", "", name);
		handler.startElement("", "", "use", attrs);
		handler.endElement("", "", "use");
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
