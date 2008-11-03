/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
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
public class FunctionCall extends Expression implements Call, XMLGenerator {
	
	private DataReference base;
	private Identifier id;
	private List<ActualArgument> arguments;
	
	private Subprogram function;

	public Identifier getId() {
		return id;
	}
	
	public FunctionCall(DataReference dataReference) {
		this.id = dataReference.getId();
		this.base = dataReference.getBase();
		List<Subscript> sections = dataReference.getSections();
		if(sections!=null) {
			arguments = new ArrayList<ActualArgument>(sections.size());
			for(Subscript subscript: sections) {
				arguments.add(new ActualArgument(subscript));
			}
		}
		
		this.setLocation(dataReference.getLocation());
	}

	public void setArguments(List<ActualArgument> arguments) {
		this.arguments = arguments;
	}

	/**
	 * @param reference
	 * @param function
	 * @deprecated use parser action
	 */
	public FunctionCall(Reference reference, List<ActualArgument> arguments, Subprogram function) {
		super(reference.getLocation());
		//this.name = reference.getName();
		this.arguments = arguments;
		this.function = function;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.Call#getArguments()
	 */
	public List<ActualArgument> getArguments() {
		return arguments;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.Call#getCallable()
	 */
	public Callable getCallable() {
		return function;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getDimensions()
	 */
	public int getDimensions() {
		return function.getDimensions();
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getType()
	 */
	public Type getType() {
		return function.getType();
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#hasAttribute(ee.olegus.fortran.ast.Attribute.Type)
	 */
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		return function.hasAttribute(type);
	}
	
	@Override
	public String toString() {
		StringBuffer str = new StringBuffer("->"+getId().getName()+"(");
		for(ActualArgument argument: arguments) {
			str.append(" "+argument);
		}
		str.append(" )");
		return str.toString();
	}

	public Object astWalk(ASTVisitor visitor) {
		if(base!=null) {
			base.astWalk(visitor);
		}
		if(arguments!=null) {
			for(ActualArgument argument: arguments) {
				argument.astWalk(visitor);
			}
		}
		return visitor.visit(this);		
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		attrs.addAttribute("", "", "name", "", getId().getName());
		handler.startElement("", "", "call", attrs);
		
		super.generateXML(handler);
		
		if(base instanceof XMLGenerator) {
			handler.startElement("", "", "base", null);
			((XMLGenerator)base).generateXML(handler);
			handler.endElement("", "", "base");
		}
		if(arguments!=null && arguments.size()>0) {
			attrs.clear(); 
			attrs.addAttribute("", "", "count", "", ""+arguments.size());
			handler.startElement("", "", "arguments", attrs);
			for(ActualArgument arg: arguments) {
				arg.generateXML(handler);
			}
			handler.endElement("", "", "arguments");
		}
		handler.endElement("", "", "call");
	}	
}
