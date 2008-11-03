/**
 * Helper class to keep track of AST walker context (including use statements). 
 */
package ee.olegus.fortran.visitors;

import java.util.HashSet;
import java.util.Set;
import java.util.Stack;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.Model;
import ee.olegus.fortran.ast.Code;
import ee.olegus.fortran.ast.Declaration;
import ee.olegus.fortran.ast.Entity;
import ee.olegus.fortran.ast.Subprogram;
import ee.olegus.fortran.ast.TypeDeclaration;
import ee.olegus.fortran.ast.TypeShape;
import ee.olegus.fortran.ast.Use;
import ee.olegus.fortran.model.Module;

/**
 * @author olegus
 *
 */
public abstract class ASTVisitorContext implements ASTVisitor {

	static Set<String> builtIn = new HashSet<String>();
	
	static {
		builtIn.add("size");
		builtIn.add("minval");
		builtIn.add("maxval");
		builtIn.add("minloc");
		builtIn.add("maxloc");
		builtIn.add("real");
		builtIn.add("sqrt");
	}	
	
	private Model model;
	private Stack<Code> scopes = new Stack<Code>();
	
	public ASTVisitorContext() {
		this(null);
	}
	
	public ASTVisitorContext(Model model) {
		this.model = model;
	}
	
	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitor#enter(ee.olegus.fortran.ast.Code)
	 */
	public void enter(Code code) {
		scopes.push(code);
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitor#leave(ee.olegus.fortran.ast.Code)
	 */
	public void leave(Code code) {
		scopes.pop();
	}
	
	/**
	 * Is given function in current context.
	 */
	Boolean isFunction(String name) {
		return isFunction(name, scopes.size()-1);
	}
	
	private Boolean isFunction(String name, int index) {
		// TODO look for global variables
		if(index<0) {
			if(builtIn.contains(name.toLowerCase())) {
				return true;
			}
			return null;
		}
		
		Code code = scopes.get(index);
		// find symbol in local declarations
		for(Declaration decl: code.getDeclarations()) {
			if(decl instanceof TypeDeclaration) {
				TypeDeclaration tdecl = (TypeDeclaration) decl;
				for(Entity entity: tdecl.getEntities()) {
					if(entity.getName().equalsIgnoreCase(name))
						return false;
				}
			}
		}
		
		// find in local functions
		if(code.getSubprograms().containsKey(name.toLowerCase())) {
			return true;
		}
		
		// look for uses TODO consider renaming
		if(model != null)
		for(Use use: code.getUses().values()) {
			Module module = model.getModules().get(use.getName().toLowerCase());
			if(module==null)
				continue;
			// TODO use arguments
			TypeShape obj=module.getProgramUnit().getVariableOrFunction(name.toLowerCase(), null, false);
			if (obj instanceof Subprogram)
				return true;
		}
		
		// look in parent scope
		return isFunction(name, index-1); 
	}
}
