/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.SortedMap;
import java.util.TreeMap;

import org.antlr.runtime.tree.CommonTree;
import org.antlr.runtime.tree.Tree;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.AttributesImpl;

import ee.olegus.fortran.ASTUtils;
import ee.olegus.fortran.ASTVisitable;
import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.XMLGenerator;
import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;
import ee.olegus.fortran.visitors.ASTVisitorContext;

/**
 * @author olegus
 *
 */
public abstract class Code implements Scope, Locatable, WithinScope, XMLGenerator, ASTVisitable {
	
	public enum LocationType {
		CODE_START,
		USE_PART,
		DECL_PART,
		EXEC_PART,
		CODE_STOP
	}
	
	private Tree tree;
	private Scope scope;	

	private Map<String,Subprogram> subprograms = new HashMap<String,Subprogram>();
	private Map<String,Interface> interfaces = new HashMap<String,Interface>();
	private Map<String,Variable> variables = new HashMap<String,Variable>();
	private Map<String,Use> uses = new HashMap<String,Use>();

	private List<Declaration> declarations = new ArrayList<Declaration>();
	private List<Statement> constructs = new ArrayList<Statement>();

	private Location location;
	private SortedMap<Enum,Location> locations = new TreeMap<Enum, Location>();
	private String filename;
	private Map<String, Type> types = new HashMap<String, Type>(3);
	
	/**
	 *	@deprecated parse with parser action
	 */
	public Code(CommonTree tree, Scope scope) {
		this.tree = tree;
		this.scope = scope;
		this.filename = scope.getFilename();
		location = new Location(tree, this, null);
	}

	public Code() {
	}

	public List<Declaration> getDeclarations() {
		return declarations;
	}

	public Map<String, Interface> getInterfaces() {
		return interfaces;
	}

	public Map<String, Subprogram> getSubprograms() {
		return subprograms;
	}

	public Tree getTree() {
		return tree;
	}

	public Map<String, Use> getUses() {
		return uses;
	}

	public Map<String, Variable> getVariables() {
		return variables;
	}

	/**
	 * @param child
	 * @deprecated parse with parser action
	 */
	protected void parseCodeElement(CommonTree child) {
		/*
		switch(child.getType()) {
		case FortranParser.START:
			locations.put(LocationType.CODE_START, new Location(child, this, null));
			break;
		
		case FortranParser.STOP:
			locations.put(LocationType.CODE_STOP, new Location(child, this, null));
			break;

		case FortranParser.EXEC_PART:
			parseExecutableCode(child);
			if(child.startIndex != -1)
				locations.put(LocationType.EXEC_PART, new Location(child, this, null));
			break;
			
		case FortranParser.USE_PART:
			List<Use> uses = Use.parseUses(child);
			for(Use use: uses)
				this.uses.put(use.getName(), use);
			if(child.startIndex != -1)
				locations.put(LocationType.USE_PART, new Location(child, this, null));
			break;
			
		case FortranParser.DECL_PART:
			List<? extends Declaration> decls = Declaration.parseDeclarations(child, this);
			for(Declaration decl: decls) {
				declarations.add(decl);
				if(decl instanceof Variable)
					variables.put(((Variable)decl).getName(), (Variable) decl);
				else if(decl instanceof Interface)
					interfaces.put(((Interface)decl).getName(), (Interface) decl);
				else if(decl instanceof Type)
					types.put(((Type)decl).getName(), (Type) decl);
			}
			if(child.startIndex != -1) { // not empty
				locations.put(LocationType.DECL_PART, new Location(child, this, null));
			}
			break;
			
		case FortranParser.T_SUBROUTINE:
		case FortranParser.T_FUNCTION:
			Subprogram sub;
			sub = new Subprogram(child, this);
			subprograms.put(sub.getName(), sub);
			break;
		}
		*/
	}
	
	/**
	 * @param tree
	 * @deprecated parse with parser action
	 */
	private void parseExecutableCode(Tree tree) {
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			CommonTree child = (CommonTree) tree.getChild(i);
			switch(child.getType()) {
			case FortranParser.T_CALL:
				
				statements.add(new SubroutineCall(child, this)); // call funname ..
				break;
				
			case FortranParser.EXEC:
				statements.add(new Executable(child, this));
			}
			
		}
		*/
	}

	public Scope getScope() {
		return scope;
	}
	
	public String toLongString() {
		StringBuffer str = new StringBuffer();
		str.append(" *USE");
		for (Iterator iter = uses.values().iterator(); iter.hasNext();) {
			str.append(" ");
			Use use = (Use) iter.next();
			str.append(use);
		}
		str.append("\n");

		for (Interface iface : interfaces.values()) {
			str.append(iface);
		}

		for (Iterator<Declaration> iter = declarations.iterator(); iter.hasNext();) {
			Declaration decl = iter.next();
			str.append(decl+"\n");
		}		
		
		
		for (Statement st: constructs) {
			str.append("\n  "+st);
		}
		
		for (Iterator iter = subprograms.values().iterator(); iter.hasNext();) {
			str.append("  ");
			Subprogram subprogram = (Subprogram) iter.next();
			str.append(subprogram);
			str.append("\n");
		}
		
		return str.toString();
	}

	public ProgramUnit getModule(String name) {
		return scope.getModule(name);
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.Scope#getSubroutine(java.lang.String, java.util.List)
	 */
	public Subprogram getSubroutine(String name, List<? extends TypeShape> arguments,  boolean immediateScope) {
		Subprogram sub = subprograms.get(name);
		if(sub!=null) {
			if(arguments == null) // do not care about arguments
				return sub;
			
			if(arguments.equals(sub.getArgumentLists().iterator().next())) // argument types match
				return sub;
		}
		
		// look interfaces
		Interface iface = interfaces.get(name);
		if(iface!=null) { // TODO how to deal with interfaces
			Callable callable = iface.getCallable(this, arguments);
			if(callable instanceof Subprogram)
				return (Subprogram) callable;
		}
		
		// look in used modules
		for(Use use: uses.values()) {
			String rename = use.getRenaming(name);
			if(rename != null) {
				// name is explicitly imported
				return getModule(use.getName()).getSubroutine(rename, arguments, immediateScope);
			}
			// module is imported as a whole
			ProgramUnit module = getModule(use.getName());
			if(module==null) continue;
			Subprogram subprogram = module.getSubroutine(name, arguments, immediateScope);
			if(subprogram != null)
				return subprogram;
		}
		
		// look in containing code
		if(scope!=null)
			return scope.getSubroutine(name, arguments, immediateScope);
		
		return null;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.Scope#getVariableOrFunction(java.lang.String, java.util.List)
	 */
	public TypeShape getVariableOrFunction(String name, List<? extends TypeShape> arguments, boolean immediateScope) {
		Variable variable = variables.get(name);
		if(variable!=null) return variable;
		
		Subprogram function = subprograms.get(name);
		if(function!=null)
			return function;
		
		// look in used modules
		for(Use use: uses.values()) {
			String rename = use.getRenaming(name);
			if(rename != null) {
				// name is explicitly imported
				return getModule(use.getName()).getSubroutine(rename, arguments, immediateScope);
			}
			// module is imported as a whole
			ProgramUnit module = getModule(use.getName());
			if(module==null) continue;
			TypeShape typeShape = module.getVariableOrFunction(name, arguments, immediateScope);
			if(typeShape!=null)
				return typeShape;
		}
		
		// look in containing code
		if(scope!=null)
			return scope.getVariableOrFunction(name, arguments, immediateScope);
		
		return null;		
	}

	public List<Statement> getConstructs() {
		return constructs;
	}

	public Location getLocation() {
		if(location == null) {
			location = new Location();
		}
		return location;
	}
	
	public Location getLocation(LocationType constant) {
		return locations.get(constant);
	}	
	
	/**
	 * @return return either location itself or element just above it
	 */
	public Location getUpperLocation(LocationType constant) {
		Location loc = locations.get(constant);
		if(loc != null) return loc;
		
		SortedMap<Enum,Location> headMap = locations.headMap(constant);
		if(!headMap.isEmpty()) return headMap.get(headMap.lastKey());
		
		return null;
	}

	public Type getType(String name) {
		if(types.containsKey(name))
			return types.get(name);
		
		// look in uses
		for(Use use: uses.values()) {
			ProgramUnit unit = getScope().getModule(use.getName());
			if(unit==null) // may be external module like MPI
				continue;
			Type type = unit.getType(name);
			if(type!=null)
				return type;
			
			// search recursively
			// TODO omptimize to search every unit only once
			//unit.getT
		}
		
		if(scope != null)
			return scope.getType(name);
		
		return null;
	}

	public SortedMap<Enum, Location> getLocations() {
		return locations;
	}

	public String getFilename() {
		return filename;
	}

	public void setDeclarations(List<Declaration> declarations) {
		this.declarations = declarations;
	}

	public void setInterfaces(Map<String, Interface> interfaces) {
		this.interfaces = interfaces;
	}

	public void setConstructs(List<Statement> statements) {
		this.constructs = statements;
	}

	public void setSubprograms(Map<String, Subprogram> subprograms) {
		this.subprograms = subprograms;
	}

	public void setUses(Map<String, Use> uses) {
		this.uses = uses;
	}
	
	public void addSubprograms(List<Subprogram> subs) {
		for(Subprogram subprogram: subs)
			subprograms.put(subprogram.getName().toLowerCase(), subprogram);
	}

	public void addUses(List<Use> uses) {
		for(Use use: uses) {
			this.uses.put(use.getName().toLowerCase(), use);
		}
	}

	public void generateXML(ContentHandler handler) throws SAXException {
		AttributesImpl attrs = new AttributesImpl();
		for(Use use: getUses().values()) {
			use.generateXML(handler);
		}

		if(getDeclarations().size() != 0) {
			attrs.clear();
			attrs.addAttribute("", "", "type", "", "declarations");
			handler.startElement("", "", "block", attrs);
			Location location = ASTUtils.calculateBlockLocation(getDeclarations());
			if(location!=null)
				location.generateXML(handler);
			for(Statement statement: getDeclarations()) {
				if(statement instanceof XMLGenerator)
					((XMLGenerator)statement).generateXML(handler);
			}
			handler.endElement("", "", "block");			
		}
		
		if(getConstructs().size() != 0) {
			attrs.clear();
			attrs.addAttribute("", "", "type", "", "executions");
			
			handler.startElement("", "", "block", attrs);
			Location location = ASTUtils.calculateBlockLocation(getConstructs());
			if(location!=null)
				location.generateXML(handler);
			for(Statement statement: getConstructs()) {
				if(statement instanceof XMLGenerator)
					((XMLGenerator)statement).generateXML(handler);
			}
			handler.endElement("", "", "block");
		}
		
		for(Subprogram subprogram: getSubprograms().values()) {
			subprogram.generateXML(handler);
		}		
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitable#astWalk(ee.olegus.fortran.ASTVisitor)
	 */
	public Object astWalk(ASTVisitor visitor) {
		visitor.enter(this);			
		for(Use use: uses.values()) {
			use.astWalk(visitor);
			visitor.visit(use);
		}
		
		for(Statement statement: constructs) {
			statement.astWalk(visitor);
			visitor.visit(statement);
		}
		
		for(Subprogram subprogram: subprograms.values()) {
			visitor.enter(subprogram);
			subprogram.astWalk(visitor);
			visitor.leave(subprogram);
		}
		visitor.leave(this);
		
		return this;
	}
	
	public void setScope(Scope scope) {
		this.scope = scope;
	}
	
}

/**
 * @author olegus
 *
 */
class XMLCallGenerator extends ASTVisitorContext implements ASTVisitor {
	private ContentHandler handler;
	private AttributesImpl attributes = new AttributesImpl();
	
	public XMLCallGenerator(ContentHandler handler) {
		this.handler = handler;
	}

	public Expression visit(Expression expr) {
		if(expr instanceof FunctionCall) {
			attributes.clear();
			attributes.addAttribute("", "", "name", "", ((FunctionCall)expr).getId().getName());
			try {
				handler.startElement("", "", "call", attributes);
				handler.endElement("", "", "call");
			} catch (SAXException e) {
				throw new RuntimeException(e);
			}
		}
		return expr;
	}

	public Statement visit(Statement stmt) {
		if(stmt instanceof SubroutineCall) {
			attributes.clear();
			attributes.addAttribute("", "", "name", "", ((SubroutineCall)stmt).getName());
			try {
				handler.startElement("", "", "call", attributes);
				handler.endElement("", "", "call");
			} catch (SAXException e) {
				throw new RuntimeException(e);
			}
		}
		return stmt;
	}	
}
