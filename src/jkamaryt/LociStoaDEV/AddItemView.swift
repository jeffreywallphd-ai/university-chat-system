import SwiftUI

struct AddItemView: View {
    @Environment(\.presentationMode) var presentationMode
    static let priorities = ["Choose One", "Assignment", "Exam", "Project", "Reading", "Other"]
    static let Class = ["Choose One", "MIS3100", "MIS4000", "HU2130", "HU2700", "Other"]
    
    @ObservedObject var toDoList: ToDoList
    @State private var priority = ""
    @State private var classes = ""
    @State private var description = ""
    @State private var dueDate = Date()
    @State private var showingAlert = false
    
    var body: some View {
        NavigationView {
            ZStack{
                Form {
                    Picker("Type of Assignment", selection: $priority) {
                        ForEach(Self.priorities, id: \.self) { priority in
                            Text(priority)
                        }
                    }
                    Picker("Course", selection: $classes) {
                        ForEach(Self.Class, id: \.self) { Classes in Text(Classes)
                        }
                    }
                    TextField("Description (Optional)", text: $description)
                    DatePicker("Due Date", selection: $dueDate, displayedComponents: .date)
                }
                .navigationTitle("Add New Task")
                #if os(iOS)
                .navigationBarTitleDisplayMode(.inline)
                #endif
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Save") {
                            if priority != "Choose One" && classes != "Choose One" && priority.count > 0 && classes.count > 0 {
                                let item = ToDoItem(id: UUID(), priority: priority,classes: classes, description: description, dueDate: dueDate)
                                toDoList.items.append(item)
                                presentationMode.wrappedValue.dismiss()
                            }
                            else {
                                showingAlert = true
                            }
                        }
                    }
                    
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") {
                            presentationMode.wrappedValue.dismiss()
                        }
                    }
                }
            }
            .background(lociBackground)
            .scrollContentBackground(.hidden)
        }
        .alert(isPresented: $showingAlert) {
            Alert(title: Text("Error"), message: Text("You must choose a task type and course before saving"), dismissButton: .default(Text("OK")))
        }
    }
}

struct AddItemView_Previews: PreviewProvider {
    static var previews: some View {
        AddItemView(toDoList: ToDoList())
    }
}