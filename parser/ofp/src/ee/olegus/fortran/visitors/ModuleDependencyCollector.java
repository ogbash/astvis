/**
 * 
 */
package ee.olegus.fortran.visitors;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.ast.Code;
import ee.olegus.fortran.ast.Expression;
import ee.olegus.fortran.ast.ProgramUnit;
import ee.olegus.fortran.ast.Statement;
import ee.olegus.fortran.ast.Use;

/**
 * @author olegus
 *
 */
public class ModuleDependencyCollector implements ASTVisitor {
	
	private Map<String, Set<String>> dependencies = new HashMap<String, Set<String>>();
	private List<String> moduleSequence;

	private String moduleName;
	
	public List<String> getModuleSequence() {
		return moduleSequence;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitor#enter(ee.olegus.fortran.ast.Code)
	 */
	public void enter(Code code) {
		if(code instanceof ProgramUnit) {
			ProgramUnit unit = (ProgramUnit) code;
			if(unit.getUnitType()==ProgramUnit.UnitType.MODULE) {
				moduleName = unit.getName().toLowerCase();
				dependencies.put(moduleName, new HashSet<String>(4));
			}
		}
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitor#leave(ee.olegus.fortran.ast.Code)
	 */
	public void leave(Code code) {
		if(code instanceof ProgramUnit) {
			moduleName = null;
		}
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitor#visit(ee.olegus.fortran.ast.Expression)
	 */
	public Expression visit(Expression expr) {
		return expr;
	}

	public Statement visit(Statement stmt) {
		if(stmt instanceof Use && moduleName!=null) {
			dependencies.get(moduleName).add(((Use)stmt).getName().toLowerCase());
		}
		return stmt;
	}

	public Map<String, Set<String>> getDependencies() {
		return dependencies;
	}
	
	public void solveDependencies() {
		// copy map
		Map<String, Set<String>> dependencies = new HashMap<String, Set<String>>();
		for(String key: this.dependencies.keySet()) {
			dependencies.put(key, new HashSet<String>(this.dependencies.get(key)));
		}
		
		// get rid of external moduleSequence
		for(Set<String> deps: dependencies.values()) {
			Set<String> externalModules = new HashSet<String>();
			for(String dep: deps) {
				if(!dependencies.containsKey(dep))
					externalModules.add(dep);
			}
			deps.removeAll(externalModules);
		}
		
		moduleSequence = new ArrayList<String>();
		// take one without dependencies
		while(dependencies.size()>0) {
			String name = null;
			for(String key: dependencies.keySet()) {
				if(dependencies.get(key).size()==0) {
					name = key;
					break;
				}
			}
			
			if(name == null)
				throw new RuntimeException("circular dependencies in "+dependencies);
			
			dependencies.remove(name);
			moduleSequence.add(name);
			
			// remove references
			for(Set<String> deps: dependencies.values()) {
				deps.remove(name);
			}
		}
	}
}
