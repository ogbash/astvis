/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;
import org.antlr.runtime.tree.Tree;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class Interface extends Declaration implements Callable {
	private String name;
	private List<Statement> statements;

	public List<Statement> getStatements() {
		return statements;
	}

	public void setStatements(List<Statement> statements) {
		this.statements = statements;
	}

	public void setName(String name) {
		this.name = name;
	}

	public Interface(CommonTree tree, Code code) {
		super(tree, code, null);
		name = tree.getChild(0).getText();

		parseInterface(tree);
	}
	
	public Interface() {
	}

	/**
	 * @deprecated use parser action
	 */
	private void parseInterface(Tree tree) {
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			Tree child = tree.getChild(i);
			switch(child.getType()) {
			case FortranParser.MODULE_PROCEDURES:
				parseModuleProcedures(child);
			}
		}*/
	}	
	
	private void parseModuleProcedures(Tree tree) {
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			Tree child = tree.getChild(i);
			switch(child.getType()) {
			case FortranParser.T_IDENT:
				moduleProcedures.add(child.getText());
			}
		}*/
	}	
	
	@Override
	public String toString() {
		StringBuffer buffer = new StringBuffer();
		buffer.append("INTERFACE "+(name!=null?name:""));		
		return buffer.toString(); 
	}

	public String getName() {
		if(name == null)
			return "<anonymous>";
		return name;
	}

	public Callable getCallable(Scope scope, List<? extends TypeShape> arguments) {
		/*
		for(String name: moduleProcedures) {
			Subprogram subprogram = scope.getSubroutine(name, arguments, false);
			if(subprogram!=null)
				return subprogram;
		}*/
		return null;
	}

	public Collection<List<? extends TypeShape>> getArgumentLists() {
		Collection<List<? extends TypeShape>> lists = new ArrayList<List<? extends TypeShape>>(2);
		/*
		for(String name: moduleProcedures) {
			Subprogram subroutine = getLocation().code.getSubroutine(name, null, true);
			lists.addAll(subroutine.getArgumentLists());
		}*/
		return lists;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
