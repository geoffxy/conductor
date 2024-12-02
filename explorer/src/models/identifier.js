class TaskIdentifier {
  constructor(path, name) {
    this.path = path;
    this.name = name;
  }

  toString() {
    if (this.path === ".") {
      return `//:${this.name}`;
    }
    return `//${this.path}:${this.name}`;
  }
}

export default TaskIdentifier;
