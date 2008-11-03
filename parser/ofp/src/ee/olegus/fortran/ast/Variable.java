package ee.olegus.fortran.ast;

import java.util.HashMap;
import java.util.Map;

import org.antlr.runtime.tree.CommonTree;
import org.antlr.runtime.tree.Tree;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.ast.Attribute.Type;


public class Variable extends Declaration implements TypeShape {
	private String name;
	private String typeName;
	private Map<Attribute.Type,Attribute> attributes = new HashMap<Attribute.Type,Attribute>(4);
	
	private ee.olegus.fortran.ast.Type type;
	private int dimensions;
	
	public Variable(CommonTree tree, Code code, Statement statement, String typeName, Map<Attribute.Type,Attribute> attrs) {
		super(tree, code, statement);
		this.typeName = typeName;
		this.name = tree.getText();
		if(attrs != null)
			attributes.putAll(attrs);
		
		parseVariable(tree); // parse array spec and initializer
		
		if(attributes.containsKey(Type.DIMENSION));
			//dimensions = attributes.get(Type.DIMENSION).dimensions;
	}
	
	/**
	 * @deprecated parse with parser action
	 */
	private void parseVariable(Tree tree) {
		/*
		int dim = 0;
		for(int i=0; i<tree.getChildCount(); i++) {
			Tree child = tree.getChild(i);
			if(FortranParser.T_COLON==child.getType()) {
				dim++;
			}
		}
		
		if(dim>0) {
			Attribute attr = new Attribute(Type.DIMENSION);
			attr.dimensions = dim;
			attributes.put(Type.DIMENSION, attr);
		}
		*/
	}	

	@Override
	public String toString() {
		StringBuffer str = new StringBuffer(" +DECL("+typeName+" "+name+")");
		for(Attribute attr: attributes.values())
			str.append(" "+attr);
		return str.toString();
	}

	public int getDimensions() {
		return dimensions;
	}

	public ee.olegus.fortran.ast.Type getType() {
		if(type==null) {
			type = getLocation().code.getType(typeName);
		}
		return type;
	}

	public String getName() {
		return name;
	}

	public Map<Attribute.Type, Attribute> getAttributes() {
		return attributes;
	}

	public boolean hasAttribute(Type type) {
		return attributes.containsKey(type);
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
