import SwiftUI

struct AdminSettingsView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var isAuthenticated = false
    @State private var adminPin = ""
    
    // Prototype state for color pickers
    @State private var primaryColor = lociBackground
    @State private var secondaryColor = lociAccent
    
    var body: some View {
        NavigationView {
            ZStack {
                lociBackground.ignoresSafeArea().opacity(0.3)
                
                if isAuthenticated {
                    Form {
                        Section(header: Text("University Branding Colors")) {
                            ColorPicker("Primary Background", selection: $primaryColor)
                            ColorPicker("Secondary Accent", selection: $secondaryColor)
                        }
                        
                        Section(footer: Text("Changes will require an app reload to propagate globally across all student instances.")) {
                            Button("Save & Deploy to Tenant") {
                                presentationMode.wrappedValue.dismiss()
                            }
                            .foregroundColor(.blue)
                            .fontWeight(.bold)
                        }
                    }
                    .scrollContentBackground(.hidden)
                } else {
                    VStack(spacing: 20) {
                        Image(systemName: "lock.shield.fill")
                            .font(.system(size: 60))
                            .foregroundColor(lociAccent)
                            .padding(.bottom, 10)
                        
                        Text("IT Administrator Access")
                            .font(.title2.bold())
                            .foregroundColor(lociAccent)
                        
                        SecureField("Enter Admin PIN (1234)", text: $adminPin)
                            .padding()
                            .background(Color.white)
                            .cornerRadius(12)
                            .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
                        
                        Button("Authenticate") {
                            if adminPin == "1234" {
                                withAnimation { isAuthenticated = true }
                            }
                        }
                        .buttonStyle(ModernButtonStyle())
                    }
                    .padding(30)
                }
            }
            .navigationTitle(isAuthenticated ? "Tenant Settings" : "Restricted")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { presentationMode.wrappedValue.dismiss() }
                }
            }
        }
    }
}

