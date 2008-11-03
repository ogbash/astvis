/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;
import org.antlr.runtime.tree.Tree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Locatable;

/**
 * @author olegus
 *
 */
public class SubroutineCall extends Statement implements Call, Locatable, XMLGenerator {
	//private LocatableString name;
	private DataReference designator;
	private List<ActualArgument> arguments = new ArrayList<ActualArgument>();
	private Subprogram subroutine;

	public SubroutineCall() {
	}
	
	/**
	 * @deprecated use parser action 
	 */
	public SubroutineCall(CommonTree tree, Code code) {
		//this.location = new Location(tree, code, this);
		
		/*
		CommonTree subtree = (CommonTree) tree.getChild(0); 
		name = new LocatableString(subtree.getText(), subtree, code, this);
		
		for(int i=0; i<subtree.getChildCount(); i++) {
			Tree child = subtree.getChild(i);
			switch (child.getType()) {
			case FortranParser.ARGS:
				parseArguments(child);
				break;
			}
		}
		*/
	}

	
	/**
	 * @deprecated use parser action
	 */
	private void parseArguments(Tree tree) {
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			CommonTree child = (CommonTree) tree.getChild(i);
			arguments.add(Expression.parse(child, getLocation().code, null));
		}*/
	}

	@Override
	public String toString() {
		StringBuffer str = new StringBuffer("->"+designator+"(");
		for(ActualArgument argument: arguments) {
			str.append(" "+argument);
		}
		str.append(" )");
		return str.toString();
	}

	public List<ActualArgument> getArguments() {
		return arguments;
	}

	public Callable getCallable() {
		return getSubroutine();
	}

	public String getName() {
		return designator.getId().getName();
	}
	
	public Subprogram getSubroutine() {
		if(subroutine == null) {
			// resolve
			//subroutine = getLocation().code.getSubroutine(getName(), getArguments(), false);
		}
		
		return subroutine;
	}

	public DataReference getDesignator() {
		return designator;
	}

	public void setDesignator(DataReference designator) {
		this.designator = designator;
		
		if(designator.getSections()!=null) {
			for(Subscript subscript: designator.getSections()) {
				arguments.add(new ActualArgument(subscript));
			}
		}
	}

	public void setArguments(List<ActualArgument> arguments) {
		this.arguments = arguments;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "type", "", "call");
		attrs.addAttribute("", "", "name", "", designator.getId().getName());
		handler.startElement("", "", "statement", attrs);
		
		super.generateXML(handler);
		
		if(arguments.size()>0) {
			attrs.clear(); attrs.addAttribute("", "", "count", "", ""+arguments.size());
			handler.startElement("", "", "arguments", attrs);
			for(ActualArgument arg: arguments) {
				arg.generateXML(handler);
			}
			handler.endElement("", "", "arguments");
		}
		
		handler.endElement("", "", "statement");
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitable#astWalk(ee.olegus.fortran.ASTVisitor)
	 */
	public Object astWalk(ASTVisitor visitor) {
		for(ActualArgument arg: arguments) {
			arg.astWalk(visitor);
		}

		return visitor.visit(this);
	}
}
