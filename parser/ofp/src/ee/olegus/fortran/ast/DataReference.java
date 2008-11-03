/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

import org.antlr.runtime.tree.CommonTree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class DataReference extends Expression {
	
	private Scope scope;
	private Identifier id;
	/** base%name */
	private DataReference base;
	
	private Variable variable;
	private List<Subscript> sections;
	
	public DataReference(CommonTree tree, Scope scope, Statement statement) {
		super(tree, (Code)scope, statement);
		this.scope = scope;
		this.id = new Identifier(tree.getText());
	}

	/**
	 * @param base sub base of this reference
	 */
	public DataReference() {
	}

	@Override
	public String toString() {
		return (base!=null ? base+"%" : "") 
			+ id.getName()
			+ (sections!=null ? sections : "");
			
	}

	public int getDimensions() {
		Variable var = getVariable();
		if(var!=null)
			return var.getDimensions();
		else
			throw new RuntimeException("Data reference cannot resolve variable name it refers to.");
	}

	public Type getType() {
		Variable var = getVariable();
		if(var!=null)
			return var.getType();
		else
			throw new RuntimeException("Data reference cannot resolve variable name it refers to.");
	}
	
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		Variable var = getVariable();
		if(var!=null)
			return var.getAttributes().containsKey(type);
		else
			throw new RuntimeException("Data reference cannot resolve variable name it refers to.");
	}
	
	public Variable getVariable() {
		if(variable == null) {
			variable = (Variable) getScope().getVariableOrFunction(getId().getName(), null, false);
		}
		return variable;
	}

	public Identifier getId() {
		return id;
	}

	public Scope getScope() {
		return scope;
	}

	public DataReference getBase() {
		return base;
	}

	public void setBase(DataReference component) {
		this.base = component;
	}

	public void setId(Identifier id) {
		this.id = id;
	}

	public List<Subscript> getSections() {
		return sections;
	}

	public void setSections(List<Subscript> sections) {
		this.sections = sections;
	}

	public Object astWalk(ASTVisitor visitor) {
		if(base!=null)
			base.astWalk(visitor);
		
		if(sections!=null)
		for(Subscript subscript: sections) {
			subscript.astWalk(visitor);
		}
		
		return visitor.visit(this);
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		if(id!=null) {
			attrs.addAttribute("", "", "name", "", id.getName());
		}
		handler.startElement("", "", "reference", attrs);
		
		// location generation is different
		super.generateXML(handler);

		if(base instanceof XMLGenerator) {
			handler.startElement("", "", "base", null);
			((XMLGenerator)base).generateXML(handler);
			handler.endElement("", "", "base");
		}
		if(sections!=null && sections.size()>0) {
			attrs.clear();
			attrs.addAttribute("", "", "count", "", ""+sections.size());
			handler.startElement("", "", "sections", attrs);
			for(Subscript subscript: sections) {
				if(subscript instanceof XMLGenerator) {
					((XMLGenerator)subscript).generateXML(handler);
				}
			}
			handler.endElement("", "", "sections");
		}
		handler.endElement("", "", "reference");
	}

	@Override
	public Location getLocation() {
		if(location==null) {
			location = new Location();
			if(base!=null) {
				location.start = base.getLocation().start;
			} else {
				if (getId()!=null)
					location.start = getId().getLocation().start;
			}
			if (getId()!=null)
				location.stop = getId().getLocation().stop;
		}
			
		return location;
	}
}
