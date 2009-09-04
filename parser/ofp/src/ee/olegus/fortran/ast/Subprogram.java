package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;
import org.antlr.runtime.tree.Tree;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.XMLGenerator;


public class Subprogram extends Code implements Callable,TypeShape,WithinScope,XMLGenerator {
	public enum Type {
		SUBROUTINE,
		FUNCTION;
	}
	
	private Type type;
	private String name;
	private List<String> argumentNames = new ArrayList<String>();
	private List<Variable> arguments = new ArrayList<Variable>();
	
	/**
	 * @deprecated parse with parser action
	 */
	public Subprogram(CommonTree tree, Scope parent) {
		/*
		super(tree, parent);
		this.type = FortranParser.T_SUBROUTINE == tree.getType() ? Subprogram.Type.SUBROUTINE
				: Subprogram.Type.FUNCTION ;
		this.name = tree.getC	 * 
	 * @param tree
hild(0).getText();
		
		parseSubprogram();
		
		for(String name: argumentNames)
			arguments.add(getVariables().get(name));
			*/
	}

	public Subprogram() {
	}

	@Override
	public boolean equals(Object obj) {
		Subprogram p = (Subprogram) obj;
		return new EqualsBuilder().append(getScope(), p.getScope())
			.append(name, p.name)
			.isEquals();
	}

	@Override
	public int hashCode() {
		return new HashCodeBuilder().append(getScope()).append(name).toHashCode();
	}

	@Override
	public String toString() {
		StringBuffer str = new StringBuffer();
		str.append(type+" "+name+"( ");
		for (String arg: argumentNames) {
			str.append(arg+" ");
		}
		str.append(")");
		
		return str.toString();
	}
	
	/**
	 * @deprecated parse with parser action
	 */
	private void parseSubprogram() { // name ARGS? DECL_PART? EXEC_PART?
		/*
		for(int i=1; i<getTree().getChildCount(); i++) {
			CommonTree child = (CommonTree) getTree().getChild(i);
			switch(child.getType()) {
			case FortranParser.ARGS:
				parseArgs(child);
				break;
			default:
				parseCodeElement(child);
			}
		}*/
	}
	
	private void parseArgs(Tree tree) {
		for(int i=0; i<tree.getChildCount(); i++) {
			Tree child = tree.getChild(i);
			argumentNames.add(child.getText());
		}
	}

	public Collection<List<? extends TypeShape>> getArgumentLists() {
		Collection<List<? extends TypeShape>> lists = new ArrayList<List<? extends TypeShape>>(1);
		lists.add(getArguments());
		return lists;
	}

	public String getName() {
		return name;
	}
	
	public List<? extends TypeShape> getArguments() {
		return new TypeShapeList(arguments);		
	}

	public int getDimensions() {
		// TODO Auto-generated method stub, implement for function
		return 0;
	}

	public ee.olegus.fortran.ast.Type getType() {
		// TODO Auto-generated method stub, implement for function
		return null;
	}

	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		// TODO Auto-generated method stub
		return false;
	}
	
	public String getFullName() {
		if(getScope() instanceof WithinScope)
			return ((WithinScope)getScope()).getFullName()+"."+getName();
		return getName();
	}

	public void setName(String name) {
		this.name = name;
	}

	public void setType(Type type) {
		this.type = type;
	}

	public List<String> getArgumentNames() {
		return argumentNames;
	}

	public void setArgumentNames(List<String> argumentNames) {
		this.argumentNames = argumentNames;
	}

	public void setArguments(List<Variable> arguments) {
		this.arguments = arguments;
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		if(name != null)
			attrs.addAttribute("", "", "id", "", name);
		
		handler.startElement("", "", type.name().toLowerCase(), attrs);
		
		getLocation().generateXML(handler);

		attrs.clear();
		attrs.addAttribute("","","count", "", ""+argumentNames.size());
		handler.startElement("", "", "parameters", attrs);
		for(String name: argumentNames) {
			attrs.clear();
			attrs.addAttribute("","","name", "", name);
			handler.startElement("", "", "parameter", attrs);
			handler.endElement("", "", "parameter");
		}
		handler.endElement("", "", "parameters");
		
		super.generateXML(handler);
				
		handler.endElement("", "", type.name().toLowerCase());
	}

}
